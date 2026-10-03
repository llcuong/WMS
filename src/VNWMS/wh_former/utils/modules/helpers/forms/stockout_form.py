from warehouse.models import Warehouse
from wh_former.models import Former_batch_data, Former_batch_data_log, Former_stockout_form, Former_rack_bin_temp, Former_batch_data
from django.db.models import Sum

from datetime import datetime
import json

def stockout_selection(request):
    if request.GET.get('mode') == 'to_lk':
        plant_list = list(Warehouse.objects.filter(wh_code__icontains="LKNBR").values_list('wh_code', flat=True).distinct())
    else:
        plant_list = list(Warehouse.objects.filter(wh_code__icontains="MACH").values_list('wh_code', flat=True).distinct())
    selected_machine = request.POST.get('selected_machine', '') or request.GET.get('selected_machine', '')
    selected_plant = request.POST.get('selected_plant', '') or request.GET.get('selected_plant', '') or (plant_list[0] if plant_list else '')

    return plant_list, selected_machine, selected_plant


def handle_stockout_form_input(request, mode, selected_line, stock_type, stockout_form, bin):
    selected_machine = request.POST.get('selected_machine', 'NBR01')
    selected_plant = request.POST.get('selected_plant', 'NBR')

    batch_data_table = json.loads(request.POST.get("batch_data", "[]").strip() or "[]")
    basket_data_table = json.loads(request.POST.get("table_data", "[]").strip() or "[]")
    basket_lost_table = json.loads(request.POST.get("table_lost", "[]").strip() or "[]")

    bin = basket_data_table[0]['bin'] if batch_data_table else bin

    if mode == 'clean':
        stockout_form = stockout_form
    # else:
    #     if int(stock_type) == 1:
    #         stockout_form = f"GN{datetime.today().strftime('%y%m%d')}{selected_machine[-2:]}{selected_line}"
    #     elif int(stock_type) == 2:
    #         stockout_form_obj = Former_stockout_form.objects.filter(
    #             stockout_to=selected_machine, stockout_form__iendswith=selected_line
    #         ).order_by('-id').first()
    #
    #         if stockout_form_obj:
    #             stockout_form = stockout_form_obj.stockout_form
    #             selected_line = stockout_form[-2:]
    #         else:
    #             stockout_form = f"GN{datetime.today().strftime('%y%m%d')}{selected_machine[-2:]}{selected_line}"

    size = ''
    is_form_restored = False

    if mode == 'clean':
        if batch_data_table:
            size = batch_data_table[0].get('former_size', '')
        else:
            size = ''
    else:
        if int(stock_type) == 1:
            size = request.POST.get('params_size', '')
        elif int(stock_type) == 2:
            stockout_form_obj = Former_stockout_form.objects.filter(
                stockout_to=selected_machine
            ).order_by('-id').first()
            if stockout_form_obj:
                size = stockout_form_obj.former_size
                is_form_restored = True
            else:
                size = ''
    return stockout_form, size, selected_plant, selected_machine, \
           batch_data_table, basket_data_table, basket_lost_table, selected_line, is_form_restored, bin



def handle_stockout_form_create(stockout_form, machine, stockout_action, rfid_reader_ip, action, bin):
    try:
        total = (Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip, action=action, to_bin=machine)
                 .aggregate(total_basket=Sum('rack_total_basket'),
                            total_former=Sum('rack_total_former')))

        stockout_total_basket = total['total_basket']
        stockout_total_former = total['total_former']

        existing_form = Former_stockout_form.objects.filter(stockout_form=stockout_form, stockout_to=machine, stockout_action=stockout_action).first()

        batch_no_with_former_list = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip,
                                                                         action=action, to_bin=machine).values('batch_no').\
                                                                            annotate(total_former=Sum('rack_total_former')).\
                                                                            order_by('-total_former')

        if not existing_form:
            batch_no_with_most_former = batch_no_with_former_list.first()

            batch_no = batch_no_with_most_former['batch_no']
            most_batch_former_qty = batch_no_with_most_former['total_former']

            batch_no_obj = Former_batch_data.objects.filter(batch_no=batch_no).values('former_size',
                                                                                      'former_used_day').first()
            former_size = batch_no_obj['former_size']
            former_used_day = batch_no_obj['former_used_day']

            Former_stockout_form.objects.create(stockout_form=stockout_form,
                                                stockout_date=datetime.today().strftime('%Y%m%d'),
                                                stockout_action=stockout_action,
                                                stockout_to=machine,
                                                stockout_from=bin,
                                                batch_no=batch_no,
                                                former_size=former_size,
                                                stockout_total_basket=stockout_total_basket,
                                                stockout_total_former=stockout_total_former,
                                                most_batch_former_qty=most_batch_former_qty,
                                                most_batch_used_day=former_used_day,
                                                )
            return True, (batch_no, former_used_day)

        if existing_form:

            key = f'KEY{stockout_form}{existing_form.former_size}'

            batch_no_with_former_list_added = []

            batch_no_with_former_list_all = Former_batch_data_log.objects.filter(batch_sub_action_key=key)

            current_batch_dict = {item['batch_no']: item['total_former'] for item in batch_no_with_former_list}

            for batch in batch_no_with_former_list_all:
                batch_no = batch.batch_no
                batch_qty_stockout = batch.batch_qty_stockout

                current_total_former = current_batch_dict.get(batch_no, 0)

                batch_added = {
                    'batch_no': batch_no,
                    'batch_total_former_stockout': current_total_former + batch_qty_stockout
                }

                batch_no_with_former_list_added.append(batch_added)

            for current_batch in batch_no_with_former_list:
                batch_no = current_batch['batch_no']
                if not any(item['batch_no'] == batch_no for item in batch_no_with_former_list_added):
                    batch_added = {
                        'batch_no': batch_no,
                        'batch_total_former_stockout': current_batch['total_former']
                    }
                    batch_no_with_former_list_added.append(batch_added)

            batch_no_with_former_list_added.sort(key=lambda x: x['batch_total_former_stockout'], reverse=True)

            if batch_no_with_former_list.first()['batch_no'] == batch_no_with_former_list_added[0]['batch_no']:
                batch_no = batch_no_with_former_list.first()['batch_no']
            else:
                batch_no = batch_no_with_former_list_added[0]['batch_no']

            batch_no_obj = Former_batch_data.objects.filter(batch_no=batch_no).values('former_size',
                                                                                      'former_used_day').first()
            former_used_day = batch_no_obj['former_used_day']

            existing_form.batch_no = batch_no
            existing_form.stockout_total_basket += stockout_total_basket
            existing_form.stockout_total_former += stockout_total_former
            existing_form.save()

            return True, (batch_no, former_used_day)

    except Exception as e:
        return False, e


def get_former_stockout_data(existing_temp):
    if existing_temp:
        size = Former_batch_data.objects.filter(batch_no=existing_temp.batch_no).value_list('former_size', flat=True)[0]
        machine = existing_temp.to_bin
        return (size, machine)