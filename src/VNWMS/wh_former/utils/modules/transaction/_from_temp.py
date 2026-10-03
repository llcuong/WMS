from wh_former.models import Basket_master_data, Former_rack_bin_temp, Former_batch_data, Former_rack_basket_temp, \
    Former_bin_data, Former_bin_data_log, RFID_read_log, Former_batch_data_log, Former_stockout_form

from django.utils import timezone

from wh_former.utils.modules.transaction.transfer_func.process_basket_transfers import _basket_transfers
from wh_former.utils.modules.transaction.transfer_func.process_batch_update import _batch_update
from wh_former.utils.modules.transaction.transfer_func.process_clean_temp import _clean_temp
from wh_former.utils.modules.transaction.transfer_func.process_used_day import _used_day

from datetime import date, datetime
from django.db.models import Sum
from django.db import transaction

'''
1. Lấy dữ liệu tạm
2. Lấy batch
3. Tính toán Used Day
4. Chuyển từng basket
5. Cập nhật batch
6. Xóa dữ liệu tạm
'''


def Transfer_From_Temp(request, rfid_reader_ip, batch_no, action, former_used_day, operation_type,
                       stockout_form=None, stockout_to=None, stockin_form=None, stockin_from=None, stock_form_size=None):
    try:
        '''1. Lấy dữ liệu tạm'''
        bin_temp_list = Former_rack_bin_temp.objects.filter(
            rfid_reader_ip=rfid_reader_ip,
            action=action
        ).exclude(to_bin__istartswith='Z')
        if action == 'STIN':
            bin_temp_list = Former_rack_bin_temp.objects.filter(
                rfid_reader_ip=rfid_reader_ip,
                action=action
            ).exclude(from_bin__istartswith='Z')


        bin_temp_list2 = Former_rack_bin_temp.objects.filter(
            rfid_reader_ip=rfid_reader_ip,
            action=action, to_bin__istartswith='Z'
        )
        if action == 'STIN':
            bin_temp_list2 = Former_rack_bin_temp.objects.filter(
                rfid_reader_ip=rfid_reader_ip,
                action=action, from_bin__istartswith='Z'
            )


        if not bin_temp_list.exists() and not bin_temp_list2.exists():
            return False, "No temp data found for this operation"


        '''2. Lấy batch'''
        batch_no_obj = Former_batch_data.objects.get(batch_no=batch_no)


        '''3. Tính toán Used Day'''
        final_used_day = _used_day(operation_type, stockin_form, batch_no_obj, former_used_day, action)


        '''4. Chuyển từng basket'''
        batch_info, total_baskets_all, total_formers_all = _basket_transfers(
            request, bin_temp_list, batch_no, batch_no_obj, operation_type, action, batch_no_obj.former_size, final_used_day, batch_no, ''
        )

        '''5. Cập nhật batch'''
        _batch_update(batch_no, batch_no_obj, total_baskets_all, total_formers_all, final_used_day,
                                     action, request.user, operation_type, key=f'KEY{stockin_form}{batch_no_obj.former_size}', stockin_from=stockin_from)

        # _handle_stockin_form(stockin_form, former_size, total_baskets_all, total_formers_all)


        if bin_temp_list2.exists():
            bk_batch_no = batch_no[:8] + 'Z' + f"{int(final_used_day):03d}"

            bk_batch_no_obj, _created = Former_batch_data.objects.get_or_create(
                batch_no=bk_batch_no,
                defaults={
                    'former_receive_form': batch_no_obj.former_receive_form,
                    'former_size': batch_no_obj.former_size,
                    'former_vendor': batch_no_obj.former_vendor,
                    'former_type': batch_no_obj.former_type,
                    'former_surface': batch_no_obj.former_surface,
                    'former_length': batch_no_obj.former_length,
                    'former_used_day': batch_no_obj.former_used_day,
                    'former_item_no': batch_no_obj.former_item_no,
                    'former_aql': batch_no_obj.former_aql,
                    'is_active': batch_no_obj.is_active,
                    'batch_data_date': batch_no_obj.batch_data_date,
                    'batch_total_basket': 0,
                    'batch_total_former': 0,
                    'batch_total_basket_in_wh': 0,
                    'batch_total_former_in_wh': 0,
                    'create_by': request.user,
                    'update_by': request.user,

                }
            )

            bk_batch_info, bk_total_baskets_all, bk_total_formers_all = _basket_transfers(
                request, bin_temp_list2, batch_no, bk_batch_no_obj, operation_type, action, bk_batch_no_obj.former_size,
                final_used_day, bk_batch_no, ''
            )

            _batch_update(bk_batch_no, bk_batch_no_obj, bk_total_baskets_all, bk_total_formers_all, final_used_day,
                                 action, request.user, operation_type, key=f'KEY{stockin_form}{batch_no_obj.former_size}', stockin_from=stockin_from)


            '''6. Xóa dữ liệu tạm'''
        bin_temp_list = Former_rack_bin_temp.objects.filter(
            rfid_reader_ip=rfid_reader_ip,
            action=action
        )
        _clean_temp(bin_temp_list, rfid_reader_ip, batch_no, action)


        return True, f"{action} completed successfully"

    except Former_batch_data.DoesNotExist:
        return False, f"Former_batch_data with batch_no {batch_no} does not exist"
    except Exception as e:
        return False, f"Error in transfer process: {str(e)}"


def Transfer_Empty_From_Temp(request, rfid_reader_ip, action):
    try:
        with transaction.atomic():

            # 1. Get rack_bin_temp (same logic as before)
            rack_bin_qs = Former_rack_bin_temp.objects.filter(
                rfid_reader_ip=rfid_reader_ip,
                action=action
            )

            rack_bin_qs = rack_bin_qs.filter(from_bin='X')

            if not rack_bin_qs.exists():
                rack_bin_qs = rack_bin_qs.filter(to_bin='X')

            if not rack_bin_qs.exists():
                return False, "No temp data found for this operation"

            # 2. Process each rack_temp_id
            for rack_temp in rack_bin_qs:
                rack_temp_id = rack_temp.rack_temp_id
                from_bin = rack_temp.from_bin
                if action == 'STIN':
                    from_bin = 'X'

                if not rack_temp_id or not from_bin:
                    continue

                # 3. Get all baskets in this rack
                basket_temps = Former_rack_basket_temp.objects.filter(
                    rack_temp_id=rack_temp_id
                )

                if not basket_temps.exists():
                    continue

                for basket_temp in basket_temps:
                    basket_no = basket_temp.basket_no
                    basket_qty = basket_temp.basket_former_qty

                    # 4. Update Former_bin_data
                    bin_value = from_bin if action == "STIN" else rack_temp.to_bin

                    updated = Former_bin_data.objects.filter(
                        basket_no=basket_no
                    ).update(
                        basket_former_qty=basket_qty,
                        bin=bin_value
                    )

                    if not updated:
                        raise Exception(f"Basket {basket_no} not found in Former_bin_data")

                    # 5. Clear former_size in Basket_master_data
                    Basket_master_data.objects.filter(
                        basket_no=basket_no
                    ).update(
                        former_size=None
                    )

            # 6. Clean temp data
            Former_rack_basket_temp.objects.filter(
                rack_temp_id__in=rack_bin_qs.values_list('rack_temp_id', flat=True)
            ).delete()

            rack_bin_qs.delete()

            return True, f"{action} completed successfully"

    except Exception as e:
        return False, f"Error in transfer process: {str(e)}"


def Transfer_From_Temps(request, rfid_reader_ip, form_batch_no, action, former_used_day, operation_type,
                       stockout_form=None, stockout_to=None, stockin_form=None, stockin_from=None):
    try:
        '''1. Lấy dữ liệu tạm'''
        bin_temp_list_all = Former_rack_bin_temp.objects.filter(
            rfid_reader_ip=rfid_reader_ip,
            action=action,
        ).order_by('-rack_total_former', '-rack_total_basket', 'batch_no')

        if not bin_temp_list_all.exists():
            return False, "No temp data found for this operation"


        batch_no_list = bin_temp_list_all.values_list('batch_no', flat=True).distinct()

        size = Former_batch_data.objects.filter(batch_no__in=batch_no_list).values_list('former_size').distinct().first()

        max_former_batch = Former_batch_data.objects.filter(batch_no__in=batch_no_list).order_by('-batch_total_former', 'batch_no').first()

        total_stock_basket = bin_temp_list_all.aggregate(Sum('rack_total_basket'))['rack_total_basket__sum'] or 0
        total_stock_former = bin_temp_list_all.aggregate(Sum('rack_total_former'))['rack_total_former__sum'] or 0

        key = f'KEY{stockout_form}{size[0]}'
        if Former_batch_data_log.objects.filter(batch_sub_action_key=key).exists():
            max_former_batch = Former_batch_data.objects.filter(batch_no=Former_stockout_form.objects.filter(
                stockout_form=stockout_form, former_size=size[0]).values_list('batch_no', flat=True)[0]).first()

        for batch_no in batch_no_list:

            bin_temp_list = bin_temp_list_all.filter(batch_no=batch_no)

            '''2. Lấy batch'''
            batch_no_obj = Former_batch_data.objects.get(batch_no=batch_no)

            '''3. Tính toán Used Day'''
            final_used_day = _used_day(operation_type, stockout_form, batch_no_obj, former_used_day, action)

            '''4. Chuyển từng basket'''
            batch_info, total_baskets_all, total_formers_all = _basket_transfers(
                request, bin_temp_list, batch_no, max_former_batch, operation_type, action, batch_no_obj.former_size, final_used_day, form_batch_no, key
            )

            '''5. Cập nhật batch'''
            _batch_update(batch_no, batch_no_obj, total_baskets_all, total_formers_all, final_used_day,
                          action, request.user, operation_type, batch_no_list, max_former_batch, key, total_stock_basket,
                          total_stock_former, form_batch_no, stockin_from=stockin_from, stockout_to=stockout_to)

            '''6. Xóa dữ liệu tạm'''
            _clean_temp(bin_temp_list, rfid_reader_ip, batch_no, action)


        return True, f"{action} completed successfully"
    except Former_batch_data.DoesNotExist:
        return False, f"Former_batch_data with batch_no {batch_no} does not exist"
    except Exception as e:
        return False, f"Error in transfer process: {str(e)}"





