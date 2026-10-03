from django.db import transaction, DatabaseError
from wh_former.models import Basket_master_data, Former_batch_data, Former_bin_data, Former_rack_basket_temp
from users.models import CustomUser
from django.db.models import F


# from VNWMS.database import lkwms_database # Removed as not needed for ORM .using()

def handle_transit_with_batch_no(request, batch_no, scanned_item):
    basket_numbers = [item.basket_no for item in scanned_item]
    count = len(scanned_item)
    total_former_qty = sum(item.basket_former_qty for item in scanned_item)

    # --- 1. Retrieve Data from Source DB ---
    try:
        batch_data = Former_batch_data.objects.get(batch_no=batch_no)
        baskets = Basket_master_data.objects.filter(basket_no__in=basket_numbers)
        bin_data = Former_bin_data.objects.filter(basket_no__in=basket_numbers)
    except Former_batch_data.DoesNotExist:
        return False, f"Batch data for Batch No. {batch_no} not found in VNWMS."
    except Exception as e:
        return False, f"Error retrieving source data (VNWMS): {str(e)}"

    # INSERT or UPDATE SECTION (to LKWMS Database)
    # The lkwms_database() call is not needed for ORM .using('LKWMS')
    # lkwms_db = lkwms_database() # Removed

    # Test line, kept for structure
    test = Basket_master_data.objects.using('LKWMS').all()

    # We use a database transaction block for the LKWMS updates
    try:
        with transaction.atomic(using='LKWMS'):
            system_user = CustomUser.objects.using('LKWMS').get(id=33)      # 33: System user
            lk_batch_data = Former_batch_data.objects.using('LKWMS').get(batch_no=batch_no)
            if lk_batch_data:
                lk_total_basket_in_wh = lk_batch_data.batch_total_basket_in_wh + count
                lk_total_former_in_wh = lk_batch_data.batch_total_former_in_wh + total_former_qty

            # --- 2. Insert/Update Basket_master_data into LKWMS ---
            for basket in baskets:
                Basket_master_data.objects.using('LKWMS').update_or_create(
                    basket_no=basket.basket_no,
                    defaults={
                        "basket_vendor": basket.basket_vendor,
                        "basket_capacity": basket.basket_capacity,
                        "basket_length": basket.basket_length,
                        "basket_receive_qty": basket.basket_receive_qty,
                        "basket_receive_date": basket.basket_receive_date,
                        "basket_purchase_order": basket.basket_purchase_order,
                        "former_size": basket.former_size,
                        "former_used_day": basket.former_used_day,
                        "is_active": 4,  # 4 = In Transit (Borrow from other factory)
                        "is_print": basket.is_print,
                        "create_by": system_user,
                        "create_at": basket.create_at,
                    }
                )

            # --- 3. Insert/Update Former_batch_data into LKWMS ---
            Former_batch_data.objects.using('LKWMS').update_or_create(
                batch_no=batch_data.batch_no,
                defaults={
                    "group_batch": batch_data.group_batch,
                    "former_receive_form": batch_data.former_receive_form,
                    "former_size": batch_data.former_size,
                    "former_vendor": batch_data.former_vendor,
                    "former_type": batch_data.former_type,
                    "former_purchase_order": batch_data.former_purchase_order,
                    "former_surface": batch_data.former_surface,
                    "former_length": batch_data.former_length,
                    "former_used_day": batch_data.former_used_day,
                    "former_item_no": batch_data.former_item_no,
                    "former_aql": batch_data.former_aql,
                    "is_active": batch_data.is_active,
                    "batch_data_date": batch_data.batch_data_date,
                    "batch_last_stockout": batch_data.batch_last_stockout,
                    "batch_total_basket": batch_data.batch_total_basket,
                    "batch_total_basket_in_wh": F('batch_total_basket_in_wh') + count,
                    "batch_total_former": batch_data.batch_total_former,
                    "batch_total_former_in_wh": F('batch_total_former_in_wh') + total_former_qty,
                    "create_by": system_user,
                    "create_at": batch_data.create_at,
                    "update_by": system_user,
                }
            )

            # --- 4. Insert/Update Former_bin_data into LKWMS ---
            for item in bin_data:
                Former_bin_data.objects.using('LKWMS').update_or_create(
                    basket_no=item.basket_no,
                    defaults={
                        "batch_no": item.batch_no,
                        "bin": "LK",
                        "basket_former_qty": item.basket_former_qty,
                        "to_bin_key": item.to_bin_key,
                        "update_at": item.update_at,
                    }
                )

    except DatabaseError as e:
        # Catches connection issues, SQL errors, etc., specific to LKWMS
        return False, f"Database Error during LKWMS update: {str(e)}"
    except Exception as e:
        # Catch-all for any other errors during LKWMS update
        return False, f"Unexpected error during LKWMS update: {str(e)}"

    # UPDATE SECTION (in VNWMS Database - the 'default' or main connection)
    try:
        with transaction.atomic():  # Uses the default database connection (VNWMS)

            # --- 5. Update Former_bin_data in VNWMS ---
            # for item in bin_data:
            #     item.bin = "LKNBR"
            #     item.save(update_fields=['bin'])  # Use update_fields for efficiency

            # --- 6. Update Basket_master_data in VNWMS ---
            for item in baskets:
                item.is_active = 5  # 5: Lending (Use in other factory)
                item.save(update_fields=['is_active'])

    except DatabaseError as e:
        # Note: If this fails, the LKWMS updates in step 2-4 will still be committed.
        # This highlights a potential risk in multi-database transactions.
        return False, f"Database Error during VNWMS update: {str(e)}. LKWMS may be inconsistent."
    except Exception as e:
        return False, f"Unexpected error during VNWMS update: {str(e)}"

    # Return True and None (or a success message) on success
    return True, None
