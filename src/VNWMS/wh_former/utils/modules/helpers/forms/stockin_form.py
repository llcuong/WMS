from warehouse.models import Warehouse
from wh_former.models import Former_stockout_form, Former_rack_bin_temp, Former_batch_data, Former_batch_data_log
from django.db.models import Sum

from datetime import datetime
import json

def stockin_selection(request):
    plant_list = list(Warehouse.objects.filter(wh_code__icontains="MACH").values_list('wh_code', flat=True).distinct())
    selected_machine = request.POST.get('selected_machine', '') or request.GET.get('selected_machine', '')
    selected_plant = request.POST.get('selected_plant', '') or request.GET.get('selected_plant', '') or (plant_list[0] if plant_list else '')

    return plant_list, selected_machine, selected_plant


def handle_stockin_form_input(request):
    selected_machine = request.POST.get('selected_machine', 'NBR01')
    selected_plant = request.POST.get('selected_plant', 'NBR')

    basket_data_table = json.loads(request.POST.get("table_data", "[]"))
    batch_data_table = json.loads(request.POST.get("batch_data", "[]"))
    basket_lost_table = json.loads(request.POST.get("table_lost", "[]"))

    stockin_form = request.POST.get('stock_form', '')

    return stockin_form, selected_plant, selected_machine, \
           batch_data_table, basket_data_table, basket_lost_table


def handle_stockout_form_update(stockin_form, former_size, selected_machine, rfid_reader_ip, action):
    try:
        original_action = action
        if selected_machine == 'CLEAN':
            stock_form_obj = Former_stockout_form.objects.filter(stockout_form=stockin_form,
                                                                 stockout_to=selected_machine).first()
            former_size = stock_form_obj.former_size
            action = 'CLEN'
        else:
            stock_form_obj = Former_stockout_form.objects.filter(stockout_form=stockin_form, former_size=former_size,
                                                                 stockout_to=selected_machine).first()
            action = 'STOU'
        batch_no = stock_form_obj.batch_no

        rack_bin_obj = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip, action=original_action)

        total_basket = rack_bin_obj.aggregate(total=Sum('rack_total_basket'))['total'] or 0
        total_former = rack_bin_obj.aggregate(total=Sum('rack_total_former'))['total'] or 0


        stock_form_obj.stockout_return_basket += total_basket
        stock_form_obj.stockout_return_former += total_former
        if not stock_form_obj.stockin_date:
            stock_form_obj.stockin_date = datetime.today().date().strftime('%Y-%m-%d')

        stock_form_obj.save()
        #
        # log_batch_no = Former_batch_data_log.objects.filter(batch_sub_action_key=f'KEY{stockin_form}{former_size}',
        #                                                      batch_action_name=action, batch_sub_action_name='MERGE'
        #                                                      ).values_list('batch_no', flat=True)[0]

        former_used_day = stock_form_obj.most_batch_used_day

        # print(f'stock_form_obj.most_batch_used_day -> |{stock_form_obj.most_batch_used_day}|')
            # Former_batch_data.objects.filter(batch_no=log_batch_no
            #                              ).values_list('former_used_day', flat=True)[0]

        if selected_machine == 'CLEAN':
            former_used_day = former_used_day
        else:
            former_used_day = former_used_day + (datetime.today().date() - stock_form_obj.stockout_date).days

        return True, (batch_no, former_used_day)
    except Exception as e:
        return False, e