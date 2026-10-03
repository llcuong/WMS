from django.db.models import Max, Sum
from django.db import transaction
from wh_former.models import Former_rack_bin_temp, Former_rack_basket_temp, Former_stockout_form, Former_bin_data

from datetime import datetime

def Transfer_To_Temp(request, basket_data_table, rfid_reader_ip, batch_no, client_ip, pid, from_bin, to_bin, action, stock_form):
    if not basket_data_table:
        return 0, 0, 0

    if basket_data_table:
        batch_scanned = Former_rack_bin_temp.objects.filter(
            rfid_reader_ip=rfid_reader_ip,
            action=action,
            batch_no=batch_no,
        )

        max_order = batch_scanned.aggregate(max_order=Max('rack_scan_order'))['max_order']
        current_order = (max_order or 0) + 1

        rack_temp_id = f"R{action}{datetime.now().strftime('%Y%m%d%H%M%S')}{batch_no}"

        Former_rack_bin_temp.objects.create(
            client_device_ip=client_ip,
            rfid_reader_ip=rfid_reader_ip,
            pid=pid,
            batch_no=batch_no,
            action=action,
            rack_temp_id=rack_temp_id,
            rack_scan_order=current_order,
            rack_total_basket=len(basket_data_table),
            rack_total_former=sum(int(basket_data_row['former_qty']) for basket_data_row in basket_data_table),
            from_bin=from_bin,
            to_bin=to_bin,
            stock_form=stock_form
        )

        for basket_data_row in basket_data_table:
            Former_rack_basket_temp.objects.create(
                rack_temp_id=rack_temp_id,
                basket_no=basket_data_row['basket_no'],
                basket_former_qty=basket_data_row['former_qty'],
                batch_no=batch_no,
            )

        total_basket_scanned = batch_scanned.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
        total_former_scanned = batch_scanned.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

        return current_order, total_basket_scanned, total_former_scanned


def Transfer_To_Temps(request, basket_data_table, rfid_reader_ip, client_ip, pid, from_bin, to_bin, action, stock_form):
    if not basket_data_table:
        return 0, 0, 0

    rack_temp_id = f"R{action}{datetime.now().strftime('%Y%m%d%H%M%S')}{to_bin}"
    batch_scanned = Former_rack_bin_temp.objects.filter(
        rfid_reader_ip=rfid_reader_ip,
        action=action,
    )
    max_order = batch_scanned.aggregate(max_order=Max('rack_scan_order'))['max_order']
    current_order = (max_order or 0) + 1
    batch_no_dict = {}

    for basket_data_row in basket_data_table:
        if action == 'STIN':
            if stock_form:
                batch_no = Former_stockout_form.objects.filter(stockout_form=stock_form).values_list('batch_no').first()[0]
            else:
                batch_no = Former_bin_data.objects.filter(basket_no=basket_data_row['basket_no']).values_list('batch_no').first()[0]
        else:
            batch_no = Former_bin_data.objects.filter(basket_no=basket_data_row['basket_no']).values_list('batch_no').first()[0]

        obj, created = Former_rack_bin_temp.objects.update_or_create(
            batch_no=batch_no,
            rfid_reader_ip=rfid_reader_ip,
            action=action,
            rack_scan_order=current_order,
            defaults={
                'client_device_ip': client_ip,
                'pid': pid,
                'rack_temp_id': rack_temp_id,
                'from_bin': from_bin,
                'to_bin': to_bin,
                'stock_form': stock_form
            }
        )

        obj.rack_total_basket = (obj.rack_total_basket or 0) + 1
        obj.rack_total_former = (obj.rack_total_former or 0) + int(basket_data_row['former_qty'])
        obj.save()

        Former_rack_basket_temp.objects.create(
            rack_temp_id=rack_temp_id,
            basket_no=basket_data_row['basket_no'],
            basket_former_qty=basket_data_row['former_qty'],
            batch_no=batch_no,
        )

        batch_no_dict[batch_no] = {
            'rack_total_basket': obj.rack_total_basket,
            'rack_total_former': obj.rack_total_former
        }

    total_basket_scanned = batch_scanned.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
    total_former_scanned = batch_scanned.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

    return current_order, total_basket_scanned, total_former_scanned