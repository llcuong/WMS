from django.views.decorators.csrf import csrf_exempt
from wh_former.models import Former_bin_data, Former_stockout_form, Former_rack_basket_temp
from warehouse.models import Area, Bin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F
from django.views.decorators.http import require_GET

from VNWMS.database import mes_database, database
from warehouse.models import Warehouse

import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

import random
import string
from datetime import datetime, date, timedelta

def get_machine_by_plant_api(request):
    plant = request.GET.get('plant')
    mode = request.GET.get('mode')
    machines = list(Area.objects.filter(warehouse_id=plant).values_list('area_id', flat=True).distinct())

    if mode == 'change' or mode == 'more':
        machines = machines[1:]
    elif mode == 'clean':
        machines = machines[:1]
    
    return JsonResponse({'machines': list(machines)})


def get_plant_by_mode_api(request):
    plant_list = list(Warehouse.objects.filter(wh_code__icontains="MACH").values_list('wh_code', flat=True).distinct())
    return JsonResponse({'plants': plant_list})


def get_line_by_machine_api(request):
    machine = request.GET.get('machine')
    lines = list(Bin.objects.filter(area__area_id=machine).values_list('bin_id', flat=True).distinct())
    
    return JsonResponse({'lines': list(lines)})



def get_wo_by_line_api(request):
    line = str(request.GET.get('line'))
    mode = request.GET.get('mode', 'init').lower()

    _mach_plant = line[:-4]
    _mach_code = line[-4:-2]
    _line = line[-2:]

    sql = f"""SELECT DISTINCT wo.Id, wo.ProductItem, std.Size, wo.AQL
              FROM [PMGMES].[dbo].[PMG_MES_WorkOrder] wo
              INNER JOIN [PMGMES].[dbo].[PMG_MES_RunCard] rc
              ON wo.Id = rc.WorkOrderId AND rc.LineName = '{_line}'
              INNER JOIN [PMGMES].[dbo].[PMG_DML_DataModelList] dml
              ON wo.MachineId = dml.Id
              INNER JOIN [PMGMES].[dbo].[PMG_MES_{_mach_plant}_SCADA_Std] std
              ON std.PartNo = wo.PartNo
              WHERE 
                 dml.DataModelTypeId = 'DMT000003'
                 AND dml.Name LIKE '%{_mach_plant}%' 
                 AND dml.Name LIKE '%{_mach_code}%'
                 AND ((rc.InspectionDate = CAST(GETDATE() AS date) AND rc.Period > 5)
                 OR (rc.InspectionDate = CAST(DATEADD(day, 1, GETDATE()) AS date) AND rc.Period < 6))"""
    if mode == 'change':
        sql += "AND wo.StartDate is NULL"

    wo = mes_database().select_sql(sql)
    return JsonResponse(wo, safe=False)



@login_required
def get_stockout_forms_api(request):
    machine = request.GET.get('machine')
    if machine == "CLEAN":
        qs = (
            Former_stockout_form.objects
                .filter(
                    stockout_to="CLEAN",
                    stockout_date__gte=timezone.now() - timezone.timedelta(days=7)
                )
                .exclude(stockout_total_former__lt=F('stockout_return_former') + 5)
                .order_by('-id')
                .values('stockout_form', 'former_size', 'stockout_total_former', 'stockout_date', 'stockin_date')
        )
        data = []
        for item in reversed(list(qs)):
            data.append(f"{item['stockout_form']}")
    else:
        qs = (
            Former_stockout_form.objects
                .filter(stockout_to=machine)
                .order_by('-id')
                .values('stockout_form', 'former_size', 'stockout_total_former', 'stockout_return_former', 'stockin_date')
        )[:2]
        
        filtered_qs = [item for item in qs if item['stockout_total_former'] - item['stockout_return_former'] >= 5]
        filtered_filtered_qs = []

        for item in filtered_qs:
            stockin_date = item['stockin_date']
            if stockin_date:
                diff_days = (date.today() - stockin_date).days
                if diff_days <= 2:
                    filtered_filtered_qs.append(item)

        if len(filtered_filtered_qs) == 0:
            if len(filtered_qs) != 0:
                filtered_filtered_qs.append(filtered_qs[0])

        data = []
        for item in reversed(filtered_filtered_qs):
            data.append(f"{item['stockout_form']}({item['former_size'] or ''})")
    return JsonResponse(data, safe=False)


@csrf_exempt
def get_stockin_choice_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        stockin_choice = data.get('stockin_choice')
        return JsonResponse({'result': 'ok', 'choice': stockin_choice})
    return JsonResponse({'error': 'Invalid request'}, status=400)



@require_POST
def get_lost_basket_api(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    epc_list = payload.get('epc_list')
    batch_no = payload.get('batch_list')
    if not isinstance(epc_list, list) or batch_no is None:
        return HttpResponseBadRequest("Payload must include 'epcs' list and 'batch_no'")
    lost_list = []
    if batch_no:
        for batch in batch_no:
            rack_basket = set(
                Former_rack_basket_temp.objects.filter(batch_no=batch).values_list('basket_no', flat=True)
            )

            lost_qs = (
                Former_bin_data.objects
                    .filter(batch_no=batch)
                    .exclude(basket_no__in=epc_list)
                    .exclude(basket_no__in=rack_basket)
                    .filter(bin__startswith='NBR')
                    .values('basket_no', 'basket_former_qty', 'bin')
            )
            lost_list.append(list(lost_qs))

    return JsonResponse({'lost': lost_list, 'lost_former': 100, 'lost_bastet': 100})


@login_required
def get_stockout_form_total_former_api(request):
    stockout_form = request.GET.get('stock_form')
    obj = Former_stockout_form.objects.filter(stockout_form=stockout_form).first()
    total_former = obj.total_former if obj else None
    # print(f"[User selected] stock_form: {stockout_form}, total_former: {total_former}")
    return JsonResponse({'total_former': total_former})


@login_required
def print_total_former_on_select_api(request):
    stockout_form = request.GET.get('stock_form')
    obj = Former_stockout_form.objects.filter(stockout_form=stockout_form).first()
    total_former = obj.stockout_total_former - obj.stockout_return_former if obj else 0
    # print(f"[User selected] stock_form: {stockout_form}, total_former: {total_former}")
    return JsonResponse({'total_former': total_former})


@require_GET
def generate_stock_form_api(request):
    previous = request.session.get('stock_form')
    pre_machine = (previous or {}).get('machine')  # CŨ
    pre_line_name = (previous or {}).get('line_name')  # CŨ
    pre_stock_type = (previous or {}).get('stock_type')  # CŨ
    pre_id_stock_form = (previous or {}).get('id_stock_form')  # CŨ
    pre_size_name_input = (previous or {}).get('size_name_input')  # CŨ

    q_machine = request.GET.get('machine')  # MỚI
    q_line_name = request.GET.get('line_name')  # MỚI
    q_stock_type = request.GET.get('stock_type')  # MỚI
    q_existing_form = request.GET.get('existing_form')  # MỚI
    q_id_stock_form = request.GET.get('id_stock_form')  # MỚI
    q_size_name_input = request.GET.get('size_name_input')  # MỚI

    machine = q_machine if q_machine is not None else (previous or {}).get('machine', '')
    line_name = q_line_name if q_line_name is not None else (previous or {}).get('line_name', '')
    stock_type = q_stock_type if q_stock_type is not None else (previous or {}).get('stock_type', '1')
    existing_form = q_existing_form if q_existing_form is not None else (previous or {}).get('existing_form', '')
    id_stock_form = q_id_stock_form if q_id_stock_form is not None else (previous or {}).get('id_stock_form', '')
    size_name_input = q_size_name_input if q_size_name_input is not None else (previous or {}).get('size_name_input', '')

    call_by_button = int(request.GET.get('call_by_button', 0))  # Default to 0
    # print(f'call_by_button = {call_by_button}')

    form_size = size_name_input
    print(f'machine -> {machine}')
    print(f'pre_machine -> {pre_machine}')

    print(f'line_name -> {line_name}')
    print(f'pre_line_name -> {pre_line_name}')

    d = datetime.now()
    yy = str(d.year)[-2:]
    mm = str(d.month).zfill(2)
    dd = str(d.day).zfill(2)
    ss = str(d.second).zfill(2)
    button_mode = 0

    if machine == 'CLEAN':
        sql = f"""
            SELECT *
            FROM [GDWMS].[dbo].[wh_former_former_rack_bin_temp]
            where action='CLEN'
        """
        rows = database().select_sql_dict(sql)
        if rows:
            form_name = rows[0]['stock_form']
        else:
            prefix = 'CL'
            if pre_id_stock_form:
                if machine == pre_machine:
                    form_name = pre_id_stock_form
                else:
                    form_name = prefix + yy + ss + mm + dd + ''.join(random.choices(string.ascii_uppercase, k=2))
            else:
                form_name = prefix + yy + ss + mm + dd + ''.join(random.choices(string.ascii_uppercase, k=2))
            # print(form_name)
    elif machine == 'LKNBR':
        sql = f"""
             SELECT *
             FROM [GDWMS].[dbo].[wh_former_former_rack_bin_temp]
             where from_bin ='LKNBR' or to_bin='LKNBR'
         """
        rows = database().select_sql_dict(sql)
        if rows:
            form_name = rows[0]['stock_form']
        else:
            prefix = 'LN'
            if pre_id_stock_form:
                if machine == pre_machine:
                    form_name = pre_id_stock_form
                else:
                    form_name = prefix + yy + ss + mm + dd + ''.join(random.choices(string.ascii_uppercase, k=2))
            else:
                form_name = prefix + yy + ss + mm + dd + ''.join(random.choices(string.ascii_uppercase, k=2))
            # print(form_name)

    else:
        sql = f"""
            SELECT TOP 1 *
            FROM [GDWMS].[dbo].[wh_former_former_stockout_form]
            WHERE stockout_to = '{machine}'
              AND stockout_form LIKE '%{line_name}%'
            ORDER BY id DESC;
        """

        rows = database().select_sql_dict(sql)
        if (rows and int(rows[0]['stockout_total_basket']) > 1) or len(rows) == 0:
            if rows and int(rows[0]['stockout_total_basket']) > 1:
                if int(call_by_button) == 1:
                    prefix = 'GN'
                    if machine == pre_machine:
                        if line_name == pre_line_name:
                            if pre_id_stock_form:
                                form_name = pre_id_stock_form
                            else:
                                form_name = prefix + yy + mm + dd + machine[-2:]
                        else:
                            form_name = prefix + yy + mm + dd + machine[-2:]
                    else:
                        form_name = prefix + yy + mm + dd + machine[-2:]

                    if line_name:
                        form_name += line_name

                else:
                    form_name = rows[0]['stockout_form']
                    form_size = rows[0]['former_size']

            else:
                prefix = 'GN'
                if machine == pre_machine:
                    if line_name == pre_line_name:
                        if pre_id_stock_form:
                            form_name = pre_id_stock_form
                        else:
                            form_name = prefix + yy + mm + dd + machine[-2:]
                    else:
                        form_name = prefix + yy + mm + dd + machine[-2:]
                else:
                    form_name = prefix + yy + mm + dd + machine[-2:]

                if line_name:
                    form_name += line_name

            if len(rows) == 0:
                button_mode = 0
            elif rows and int(rows[0]['stockout_total_basket']) > 1:
                button_mode = 1

        else:
            form_name = rows[0]['stockout_form']
            form_size = rows[0]['former_size']
            button_mode = 1
    #
    # print(form_name)
    # print(form_size)

    request.session['stock_form'] = {
        'machine': machine,
        'line_name': line_name,
        'stock_type': stock_type,
        'existing_form': existing_form,
        'id_stock_form': id_stock_form,
        'size_name_input': size_name_input,
        'button_mode': button_mode,
        'saved_at': timezone.now().isoformat(),
    }
    request.session.set_expiry(60*60*24)

    return JsonResponse({
        'success': True,
        'form_name': form_name,
        'form_size': form_size,
        'is_size_readonly': form_size != 'auto',
        'button_mode': button_mode,
    })