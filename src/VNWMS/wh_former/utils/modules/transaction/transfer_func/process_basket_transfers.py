from wh_former.models import Basket_master_data, Former_rack_bin_temp, Former_batch_data, Former_rack_basket_temp, \
    Former_bin_data, Former_bin_data_log, RFID_read_log, Former_batch_data_log, Former_stockout_form

def _basket_transfers(request, rack_bin_temps, batch_no, batch_no_obj, operation_type, action, former_size, final_used_day, form_batch_no, to_bin_key):
    batch_info = {}
    total_baskets_all = 0
    total_formers_all = 0

    for rack_bin_temp in rack_bin_temps:
        basket_temps = Former_rack_basket_temp.objects.filter(rack_temp_id=rack_bin_temp.rack_temp_id, batch_no=batch_no)
        to_bin_key = '' if operation_type == 'stockin' else to_bin_key

        for basket_temp in basket_temps:
            try:
                basket_master_obj = Basket_master_data.objects.get(basket_no=basket_temp.basket_no)
            except Basket_master_data.DoesNotExist:
                raise Exception(f"Basket {basket_temp.basket_no} not found")

            _transfer_basket(basket_master_obj, basket_temp, batch_no_obj, rack_bin_temp, final_used_day, former_size, form_batch_no, to_bin_key, operation_type, action)

            _create_log(batch_no_obj, basket_master_obj, rack_bin_temp, basket_temp, request.user, action,
                                 operation_type, former_size)

            RFID_read_log.objects.filter(basket_no=basket_temp.basket_no, is_used=False).update(is_used=True)

        if operation_type == 'stockout':
            batch_no_value = Former_batch_data.objects.filter(batch_no=form_batch_no).values_list('batch_no', flat=True).first()
            if batch_no_value:
                Former_bin_data.objects.filter(to_bin_key=to_bin_key).update(batch_no=batch_no_value)

        basket_count = basket_temps.count()
        former_count = sum(bt.basket_former_qty for bt in basket_temps)
        total_baskets_all += basket_count
        total_formers_all += former_count

    return batch_info, total_baskets_all, total_formers_all



def _transfer_basket(basket_master_obj, basket_temp, batch_no_obj, rack_bin_temp, final_used_day, former_size, form_batch_no, to_bin_key, operation_type, action):
    Former_bin_data.objects.update_or_create(
        basket_no=basket_master_obj,
        defaults={
            'batch_no': Former_batch_data.objects.filter(batch_no=form_batch_no).first(),
            'bin': rack_bin_temp.from_bin if action == 'STIN' else rack_bin_temp.to_bin,
            'basket_former_qty': basket_temp.basket_former_qty,
            'to_bin_key': to_bin_key
        }
    )

    Basket_master_data.objects.filter(basket_no=basket_temp.basket_no).update(
        is_active=1,
        former_used_day=final_used_day,
        former_size=former_size
    )



def _create_log(batch_no_obj, basket_master_obj, rack_bin_temp, basket_temp, user, action, operation_type, former_size):
    Former_bin_data_log.objects.create(
        batch_no=batch_no_obj,
        basket_no=basket_master_obj,
        from_bin=rack_bin_temp.from_bin,
        to_bin=rack_bin_temp.to_bin,
        basket_former_qty=basket_temp.basket_former_qty,
        create_by=user,
        action=action,
        action_form=operation_type,
        former_size=former_size
    )
