from django.db import transaction
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import F, Sum, Count, Max

from wh_former.models import RFID_read_log, Basket_master_data, Basket_master_data_log, \
    Former_bin_data_log, Former_batch_data, Former_bin_data, Former_stockout_form, \
    Former_rack_bin_temp, Former_rack_basket_temp, Former_batch_data_log, scrap_maintain, RFID_setting
from wh_former.forms import BasketSearchForm, FormerMasterDataForm, \
    FormerSearchForm, ManageVendorDataForm, StockDataRecordForm
from django.utils.translation import gettext_lazy as _, get_language

from wh_former.utils.helpers.epc_helpers import get_basket_series, get_basket_no
from wh_former.utils.configs.table_configs import former_search_define
from VNWMS.database import database

from django.db.models import Q


from warehouse.models import Warehouse, MovementType
import json
import re



from wh_former.forms import BasketMasterDataForm

from wh_former.utils.modules.helpers.forms.paramerters_forms import get_params_form, insert_params_form
from wh_former.utils.modules.helpers.forms.basket_form import handle_basket_master_data_form, handle_basket_search_form, handle_basket_search_query, handle_basket_edit_form
from wh_former.utils.modules.helpers.forms.former_form import get_former_batch_data, handle_former_master_data_form, handle_former_search_form, handle_former_search_query, handle_former_search_filter, handle_former_search_result, clean_former_master_data_form, get_former_stockout_data_as_dict, show_noti_modal
from wh_former.utils.modules.helpers.forms.stockout_form import stockout_selection, handle_stockout_form_input, handle_stockout_form_create
from wh_former.utils.modules.helpers.forms.stockin_form import stockin_selection, handle_stockin_form_input, handle_stockout_form_update

from wh_former.utils.modules.helpers.buttons.action_buttons import Cancel_Operation

from wh_former.utils.modules.transaction._to_temp import Transfer_To_Temp, Transfer_To_Temps
from wh_former.utils.modules.transaction._from_temp import Transfer_From_Temp, Transfer_From_Temps, Transfer_Empty_From_Temp
from wh_former.utils.modules.transaction._transit import handle_transit_with_batch_no

from wh_former.utils.modules.helpers.permissions.control_permission import get_permission
from wh_former.utils.modules.helpers.tables.table_headers import basket_master_data_table, basket_search_table, \
    former_master_data_table, basket_broken_reporting_table, former_broken_reporting_table


from django.utils.timezone import now
from django.core.paginator import Paginator
from django.http import JsonResponse
from collections import defaultdict
import datetime
from django.utils.translation import get_language


@login_required
def user_basket_master_data(request):
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()
    try:
        column_width, column_align, column_name = basket_master_data_table()
        columns = list(zip(column_name, column_width, column_align))
        results = []

        vendor_form, all_vendors = get_params_form(group='vendor', belong='basket')
        length_form, all_lengths = get_params_form(group='length', belong='basket')

        form = BasketMasterDataForm()

        total_result = 0

        if request.method == 'POST':
            form_type = request.POST.get('form_type', '').strip()

            if form_type == 'former':
                form = BasketMasterDataForm(request.POST)
                results, total_result, error_msg, success_modal, length_value, former_vendor = handle_basket_master_data_form(request, form, column_width, column_align)

                if success_modal:
                    form = BasketMasterDataForm()
                    request.session['basket_display_data'] = {
                        'results': results,
                        'total_result': total_result,
                        'success_modal': True,
                        'length_value': length_value
                    }

                    headers = [force_str(strip_tags(h)) for h in column_name]
                    request.session['basket_export'] = {
                        "headers": headers,
                        "rows": _serialize_rows(results, headers)
                    }
                    request.session.modified = True
                    return redirect(request.path)
                else:
                    error_msg = error_msg
                    error_modal = True

            elif form_type == 'vendor':
                form = BasketMasterDataForm()
                vendor_form = insert_params_form(request, group='vendor', belong='basket')
                return redirect(request.path)

            elif form_type == 'length':
                form = BasketMasterDataForm()
                length_form = insert_params_form(request, group='length', belong='basket')
                return redirect(request.path)

        if 'basket_display_data' in request.session:
            display_data = request.session.pop('basket_display_data')
            results = display_data['results']
            total_result = display_data['total_result']
            success_modal = display_data.get('success_modal', False)

    except Exception as e:
        error_msg = f"user_basket_master_data -> {e}"
        error_modal = True
    today_str = timezone.now().date().strftime('%Y-%m-%d'),
    return render(request, 'wh_former/pages/basket_master_data.html', locals())

from django.utils.encoding import force_str
from django.utils.html import strip_tags
def _serialize_rows(rows, headers):
    out = []
    for row in rows:
        if isinstance(row, dict):
            out.append([row.get(h, "") for h in headers])
        elif isinstance(row, (list, tuple)):
            out.append(list(row[:len(headers)]))
        else:
            out.append([force_str(row)])
    return out

@login_required
def user_basket_search(request):
    column_width, column_align, column_name = basket_search_table()
    columns = list(zip(column_name, column_width, column_align))
    results = []

    form = BasketSearchForm(action='search')
    length_form, all_lengths = get_params_form(group='length', belong='basket')

    if request.method == 'POST':
        success, msg = handle_basket_edit_form(request)
        if success:
            success_modal = True
            return redirect(request.path + '?' + request.GET.urlencode())
        else:
            error_modal = True
            error_msg = msg

    if request.method == 'GET':
        form = BasketSearchForm(request.GET, action='search')
        queryset = handle_basket_search_query()

        page_number = request.GET.get('page')
        if form.is_valid():
            search_result = handle_basket_search_form(form, queryset, column_width, column_align, default_filter='all')
            if len(search_result) == 6:
                results, total_result, error_msg, success_modal, former_vendor, editable_groups, basket_state = search_result
            else:
                results, total_result, error_msg, success_modal, former_vendor, editable_groups, basket_state = search_result
                editable_groups = {}
            if not success_modal:
                error_modal = True

            paginator = Paginator(results, 96)
            page_obj = paginator.get_page(page_number)
            is_paginated = page_obj.has_other_pages()
            data = page_obj.object_list

            headers = [force_str(strip_tags(h)) for h in column_name]
            request.session['basket_export'] = {
                "headers": headers,
                "rows": _serialize_rows(results, headers)
            }
            request.session.modified = True
        else:
            error_msg = form.errors
            error_modal = True

    return render(request, 'wh_former/pages/basket_search.html', locals())


def user_basket_modify(request):
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()

    column_width, column_align, column_name = basket_search_table()
    columns = list(zip(column_name, column_width, column_align))
    results = []
    editable_groups = {}

    form = BasketSearchForm(action='modify')
    length_form, all_lengths = get_params_form(group='length', belong='basket')
    if request.method == 'POST':
        success, msg = handle_basket_edit_form(request)
        if success:
            success_modal = True
            return redirect(request.path + '?' + request.GET.urlencode())
        else:
            error_modal = True
            error_msg = msg

    if request.method == 'GET':
        page_number = request.GET.get('page')

        form = BasketSearchForm(request.GET, action='modify')
        if form.is_valid():
            basket_no = request.GET.get('basket_no')
            saved_group = request.GET.get('saved_group')
            purchase_order = request.GET.get('purchase_order')
            filled_count = sum(bool(v) for v in [basket_no, saved_group, purchase_order])

            if filled_count == 1:
                queryset = handle_basket_search_query()
                results, total_result, error_msg, success_modal, former_vendor, editable_groups, basket_state = handle_basket_search_form(form, queryset,
                                                                                                           column_width, column_align, default_filter='key')

                paginator = Paginator(results, 100)
                page_obj = paginator.get_page(page_number)
                is_paginated = page_obj.has_other_pages()
                data = page_obj.object_list

                headers = [force_str(strip_tags(h)) for h in column_name]
                request.session['basket_export'] = {
                    "headers": headers,
                    "rows": _serialize_rows(results, headers)
                }
                request.session.modified = True

                if not success_modal:
                    warning_modal = True
            else:
                error_msg = 'Chỉ nhập 1 trường giá trị thôi'
                error_modal = True
        else:
            error_msg = form.errors
            error_modal = True
    return render(request, 'wh_former/pages/basket_modify.html', locals())

@login_required
def user_former_master_data(request):
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()

    result = get_permission(request)
    if isinstance(result, HttpResponse):
        has_permission_ip = False
        return result
    else:
        has_permission_ip = True

    client_ip, pid, rfid_reader_state, rfid_setting_id, gate_name, rfid_reader_ip, is_ip_allowed = result

    print(f"user_basket_modify -> rfid_reader_ip -> {rfid_reader_ip}")
    column_width, column_align, column_name = former_master_data_table()
    locations = RFID_setting.objects.filter(client_device_ip=client_ip).order_by("location_name")

    form = FormerMasterDataForm()

    vendor_form, all_vendors = get_params_form(group='vendor', belong='former')
    length_form, all_lengths = get_params_form(group='length', belong='former')
    size_form, all_sizes = get_params_form(group='size', belong=None)
    item_form, all_items = get_params_form(group='itemno', belong=None)
    surface_form, all_surfaces = get_params_form(group='surface', belong=None)

    action = MovementType.objects.get(mvt_code="CRTE").mvt_code

    existing_temps = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip,
                                                         action=action).order_by('-rack_scan_order')

    existing_temp = existing_temps.first() if existing_temps.exists() else None
    rack_scanned = existing_temp.rack_scan_order or 0 if existing_temp else 0
    total_basket = existing_temps.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
    total_former = existing_temps.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

    former_data = get_former_batch_data(request, existing_temp)

    (former_receive_form, former_size, former_vendor, batch_data_date, former_surface, length_value, former_type,
     former_purchase_order, former_item_no, former_used_day, batch_no, form_data) = former_data

    is_form_restored = bool(form_data and batch_no)

    show_process_warning = show_noti_modal(request, is_form_restored, action)

    if form_data:
        form = FormerMasterDataForm(initial=form_data)

    if request.method == 'POST':
        form_type = request.POST.get('form_type', '').strip()

        if form_type == 'former':

            former_used_day = int(former_used_day) if former_used_day else 0

            batch_no_obj, form_is_valid, error_msg = handle_former_master_data_form(request, batch_no, former_size,
                                                                                    former_vendor, former_item_no, length_value,
                                                                                    former_surface, former_type, former_receive_form,
                                                                                    former_used_day, former_purchase_order, batch_data_date)
            if form_is_valid:
                basket_data_table = json.loads(request.POST.get("table_data", "[]"))

                new_total_basket = len(basket_data_table)

                bin_id = basket_data_table[0]['bin']
                wms_db = database()
                sql = f"""
                            SELECT wa.area_id, wa.area_name, wa.pos_x, wa.pos_y, 
                                wa.area_w, wa.area_l, COUNT(wffbd.basket_no) AS total_baskets
                            FROM [GDWMS].[dbo].[warehouse_area] wa
                            LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] wffbd
                                ON wa.[area_name] = wffbd.[bin]
                            WHERE wa.[area_name] = '{bin_id}'
                            GROUP BY wa.area_id, wa.area_name, wa.pos_x, 
                                     wa.pos_y, wa.area_w, wa.area_l"""

                area_data = wms_db.select_sql_dict(sql)
                area_info = area_data[0]
                area_w = area_info['area_w']
                area_l = area_info['area_l']
                current_total_baskets = area_info['total_baskets']

                max_capacity = int((area_w * area_l * 216) / (30 * 30))
                if max_capacity > (int(current_total_baskets) + new_total_basket):

                    rack_scanned, total_basket, total_former = Transfer_To_Temp(request, basket_data_table, rfid_reader_ip, batch_no, client_ip, pid,
                                                    from_bin='INIT', to_bin=basket_data_table[0]['bin'], action=action, stock_form=former_receive_form)
                    success_modal = True

                    is_form_restored = True

                else:
                    error_modal = True
                    error_msg = 'Up limit error - Choose another area'
                    table_data_json = json.dumps(basket_data_table)
                    is_form_restored = True
                    form = FormerMasterDataForm(request.POST)
                    columns = list(zip(column_name, column_width, column_align))
                    return render(request, 'wh_former/pages/former_master_data.html', locals())

            else:
                error_modal = True

        elif form_type == 'done':
            success, error_msg = Transfer_From_Temp(request, rfid_reader_ip, batch_no, action,
                                                        former_used_day, operation_type="stockin")

            if success:
                success_modal = True
                rack_scanned = total_basket = total_former = 0
                is_form_restored = False

                (former_receive_form, former_size, former_vendor, batch_data_date, former_surface, length_value,
                 former_type, former_purchase_order, former_item_no, former_used_day, batch_no,
                 form_data) = clean_former_master_data_form()

            else:
                error_modal = True

        elif form_type == 'cancel':
            success, error_msg, total_former, total_basket = Cancel_Operation(request, rfid_reader_ip, action)

            if success or error_msg == 'No temp data found for action CRTE':
                success_modal = True
                rack_scanned = error_msg
                is_form_restored = False

                batch_no = request.POST.get('batch_no', '') or request.GET.get('batch_no', '')
                if batch_no:
                    Former_bin_data.objects.filter(batch_no__batch_no=batch_no).delete()
                    Former_batch_data_log.objects.filter(batch_no=batch_no).delete()
                    Former_batch_data.objects.filter(batch_no=batch_no).delete()

                (former_receive_form, former_size, former_vendor, batch_data_date, former_surface, length_value,
                 former_type, former_purchase_order, former_item_no, former_used_day, batch_no,
                 form_data) = clean_former_master_data_form()
            else:
                error_modal = True

        elif form_type == 'vendor':
            vendor_form = insert_params_form(request, group='vendor', belong='former')

        elif form_type == 'size':
            size_form = insert_params_form(request, group='size', belong=None)

        elif form_type == 'item':
            item_form = insert_params_form(request, group='itemno', belong=None)

        elif form_type == 'length':
            length_form = insert_params_form(request, group='length', belong='former')

        elif form_type == 'surface':
            surface_form = insert_params_form(request, group='surface', belong=None)

    epcs = RFID_read_log.objects.filter(client_device_ip=client_ip, is_used=False, pid=pid)
    columns = list(zip(column_name, column_width, column_align))
    return render(request, 'wh_former/pages/former_master_data.html', locals())

def user_former_search(request):
    column_width, column_align, column_name = former_search_define()
    columns = list(zip(column_name, column_width, column_align))
    form = FormerSearchForm(request.GET or None)
    results = []

    former_vendor, former_item_no, former_size, length_value, former_surface, former_type = handle_former_search_form(request)

    queryset = handle_former_search_query()

    if form.is_valid():
        queryset = handle_former_search_filter(queryset, form, former_vendor, former_item_no, former_size, length_value, former_surface, former_type)
    results = handle_former_search_result(queryset, column_width, column_align, results)

    total_baskets = len(results)
    return render(request, 'wh_former/pages/former_search.html', locals())


@login_required
def user_former_stock_out(request):
    mode = request.GET.get('mode', 'init').lower()
    stock_type = request.GET.get('stock_type', '1')
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()

    result = get_permission(request)
    if isinstance(result, HttpResponse):
        if is_wh_former_admin:
            has_permission_ip = True
        else:
            has_permission_ip = False
            return result
    else:
        has_permission_ip = True

    client_ip, pid, rfid_reader_state, rfid_setting_id, gate_name, rfid_reader_ip, is_ip_allowed = result
    column_width, column_align, column_name = former_master_data_table()
    locations = RFID_setting.objects.filter(client_device_ip=client_ip).order_by("location_name")

    if mode == 'clean':
        action = MovementType.objects.get(mvt_code="CLEN").mvt_code
    else:
        action = MovementType.objects.get(mvt_code="STOU").mvt_code

    existing_temps = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip,
                                                         action=action).order_by('-rack_scan_order')

    existing_temp = existing_temps.first() if existing_temps.exists() else None
    rack_scanned = existing_temp.rack_scan_order or 0 if existing_temp else 0
    total_basket = existing_temps.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
    total_former = existing_temps.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

    bin_codes = (
        Former_bin_data.objects.exclude(Q(bin__startswith='NBR') | Q(bin='X')).values_list('bin', flat=True).distinct()
    )

    bin = (
        Former_rack_bin_temp.objects
            .filter(rfid_reader_ip=rfid_reader_ip, action=action)
            .exclude(Q(from_bin__isnull=True) | Q(from_bin__exact='') | Q(from_bin__icontains='z'))
            .order_by('-rack_scan_order')
            .values_list('from_bin', flat=True)
            .first()
    )
    stockout_data = get_former_stockout_data_as_dict(existing_temp)
    former_size = stockout_data['params_size']
    stockout_form = stockout_data['stockout_form']
    selected_line = 'A1'

    if not existing_temp:
        stockout_form = request.POST.get('stockout_form')
        former_size = request.POST.get('params_size')

    form_initial = {}
    if stockout_form:
        form_initial['stockout_form'] = stockout_form
        selected_line = stockout_form[-2:]

    if former_size:
        form_initial['size'] = former_size

    form = StockDataRecordForm(initial=form_initial)

    plants, selected_machine, selected_plant = stockout_selection(request)

    if not selected_machine and stockout_data['selected_machine']:
        selected_machine = stockout_data['selected_machine']
    if not selected_plant and stockout_data['selected_plant']:
        selected_plant = stockout_data['selected_plant']

    if mode != 'init':
        is_form_restored = bool(stockout_form)
        show_process_warning = show_noti_modal(request, is_form_restored, action)


    if request.method == 'POST':

        stockout_form, former_size, selected_plant, selected_machine, \
        batch_data_table, basket_data_table, basket_lost_table, selected_line, is_form_restored, bin = handle_stockout_form_input(request, mode, selected_line, stock_type, stockout_form, bin)

        form_type = request.POST.get('form_type', '').strip()
        if form_type == 'former':
            rack_scanned, total_basket, total_former = Transfer_To_Temps(request, basket_data_table, rfid_reader_ip,
                                                                        client_ip, pid,
                                                                        from_bin=bin,
                                                                        to_bin=selected_machine,
                                                                        action=action,
                                                                        stock_form=stockout_form)
            success_modal = True

            selected_line = stockout_form[-2:]
            if mode != 'init':
                is_form_restored = True

        elif form_type == 'done':
            if mode == 'to_lk':
                scanned_item = list(Former_rack_basket_temp.objects.all())

            success, msg = handle_stockout_form_create(stockout_form, selected_machine, 'to_machine', rfid_reader_ip, action, bin)

            if not success:
                error_msg = msg
                error_modal = True

            (batch_no, former_used_day) = msg

            success, error_msg = Transfer_From_Temps(request, rfid_reader_ip, batch_no, action,
                                                    former_used_day, operation_type="stockout", stockout_form=stockout_form, stockout_to=selected_machine)

            if mode == 'to_lk':
                handle_transit_with_batch_no(request, batch_no, scanned_item)

            if success:
                success_modal = True
                rack_scanned = total_basket = total_former = 0
                selected_line = 'A1'
                selected_machine = ''
                is_form_restored = False


        elif form_type == 'cancel':
            success, error_msg, total_former, total_basket = Cancel_Operation(request, rfid_reader_ip, action)

            if success:
                success_modal = True
                rack_scanned = error_msg

                stockout_form = request.POST.get('stockout_form', '') or request.GET.get('stockout_form', '')
                if stockout_form:
                    Former_stockout_form.objects.filter(stockout_form=stockout_form).delete()
                selected_line = 'A1'

                is_form_restored = False
            else:
                error_modal = True
    columns = list(zip(column_name, column_width, column_align))
    return render(request, 'wh_former/pages/former_stock_out.html', {**locals(), 'stockout': True})


@login_required
def user_former_stock_out_empty(request):
    mode = request.GET.get('mode', 'init').lower()
    stock_type = request.GET.get('stock_type', '1')
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()

    result = get_permission(request)
    if isinstance(result, HttpResponse):
        if is_wh_former_admin:
            has_permission_ip = True
        else:
            has_permission_ip = False
            return result
    else:
        has_permission_ip = True

    client_ip, pid, rfid_reader_state, rfid_setting_id, gate_name, rfid_reader_ip, is_ip_allowed = result
    column_width, column_align, column_name = former_master_data_table()
    locations = RFID_setting.objects.filter(client_device_ip=client_ip).order_by("location_name")

    if mode == 'clean':
        action = MovementType.objects.get(mvt_code="CLEN").mvt_code
    else:
        action = MovementType.objects.get(mvt_code="STOU").mvt_code

    existing_temps = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip,
                                                         action=action).order_by('-rack_scan_order')

    existing_temp = existing_temps.first() if existing_temps.exists() else None
    rack_scanned = existing_temp.rack_scan_order or 0 if existing_temp else 0
    total_basket = existing_temps.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
    total_former = existing_temps.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

    bin_codes = Former_bin_data.objects.all().values_list("bin", flat=True).distinct()

    bin = (
        Former_rack_bin_temp.objects
            .filter(rfid_reader_ip=rfid_reader_ip, action=action)
            .exclude(Q(from_bin__isnull=True) | Q(from_bin__exact='') | Q(from_bin__icontains='z'))
            .order_by('-rack_scan_order')
            .values_list('from_bin', flat=True)
            .first()
    )
    stockout_data = get_former_stockout_data_as_dict(existing_temp)
    former_size = stockout_data['params_size']
    stockout_form = stockout_data['stockout_form']
    selected_line = 'A1'

    if not existing_temp:
        stockout_form = request.POST.get('stockout_form')
        former_size = request.POST.get('params_size')

    form_initial = {}
    if stockout_form:
        form_initial['stockout_form'] = stockout_form
        selected_line = stockout_form[-2:]

    if former_size:
        form_initial['size'] = former_size

    form = StockDataRecordForm(initial=form_initial)

    plants, selected_machine, selected_plant = stockout_selection(request)

    if not selected_machine and stockout_data['selected_machine']:
        selected_machine = stockout_data['selected_machine']
    if not selected_plant and stockout_data['selected_plant']:
        selected_plant = stockout_data['selected_plant']

    if mode != 'init':
        is_form_restored = bool(stockout_form)
        show_process_warning = show_noti_modal(request, is_form_restored, action)


    if request.method == 'POST':

        stockout_form, former_size, selected_plant, selected_machine, \
        batch_data_table, basket_data_table, basket_lost_table, selected_line, is_form_restored, bin = handle_stockout_form_input(request, mode, selected_line, stock_type, stockout_form, bin)

        form_type = request.POST.get('form_type', '').strip()
        if form_type == 'former':
            rack_scanned, total_basket, total_former = Transfer_To_Temps(request, basket_data_table, rfid_reader_ip,
                                                                        client_ip, pid,
                                                                        from_bin=bin,
                                                                        to_bin=selected_machine,
                                                                        action=action,
                                                                        stock_form=stockout_form)
            success_modal = True

            selected_line = stockout_form[-2:]
            if mode != 'init':
                is_form_restored = True

        elif form_type == 'done':
            # if mode == 'to_lk':
            #     scanned_item = list(Former_rack_basket_temp.objects.all())
            #
            # success, msg = handle_stockout_form_create(stockout_form, selected_machine, 'to_machine', rfid_reader_ip, action, bin)
            #
            # if not success:
            #     error_msg = msg
            #     error_modal = True
            #
            # (batch_no, former_used_day) = msg

            success, error_msg = Transfer_Empty_From_Temp(request, rfid_reader_ip, action)

            # if mode == 'to_lk':
            #     handle_transit_with_batch_no(request, batch_no, scanned_item)

            if success:
                success_modal = True
                rack_scanned = total_basket = total_former = 0
                selected_line = 'A1'
                selected_machine = ''
                is_form_restored = False


        elif form_type == 'cancel':
            success, error_msg, total_former, total_basket = Cancel_Operation(request, rfid_reader_ip, action)

            if success:
                success_modal = True
                rack_scanned = error_msg

                stockout_form = request.POST.get('stockout_form', '') or request.GET.get('stockout_form', '')
                if stockout_form:
                    Former_stockout_form.objects.filter(stockout_form=stockout_form).delete()
                selected_line = 'A1'

                is_form_restored = False
            else:
                error_modal = True
    columns = list(zip(column_name, column_width, column_align))
    return render(request, 'wh_former/pages/former_stock_out_empty.html', {**locals(), 'stockout': True})


@login_required
def user_former_stock_in(request):
    mode = request.GET.get('mode', 'init').lower()
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()

    result = get_permission(request)
    if isinstance(result, HttpResponse):
        if is_wh_former_admin:
            has_permission_ip = True
        else:
            has_permission_ip = False
            return result
    else:
        has_permission_ip = True


    client_ip, pid, rfid_reader_state, rfid_setting_id, gate_name, rfid_reader_ip, is_ip_allowed = result
    column_width, column_align, column_name = former_master_data_table()
    columns = list(zip(column_name, column_width, column_align))
    locations = RFID_setting.objects.filter(client_device_ip=client_ip).order_by("location_name")

    action = MovementType.objects.get(mvt_code="STIN").mvt_code
    existing_temps = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip,
                                                         action=action).order_by('-rack_scan_order')

    existing_temp = existing_temps.first() if existing_temps.exists() else None
    rack_scanned = existing_temp.rack_scan_order or 0 if existing_temp else 0
    total_basket = existing_temps.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
    total_former = existing_temps.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

    stockout_data = get_former_stockout_data_as_dict(existing_temp)
    former_size = stockout_data['params_size']
    stockout_form = stockout_data['stockout_form']

    plants, selected_machine, selected_plant = stockin_selection(request)

    if not selected_machine and stockout_data.get('selected_machine'):
        selected_machine = stockout_data['selected_machine']
    if not selected_plant and stockout_data.get('selected_plant'):
        selected_plant = stockout_data['selected_plant']

    form_initial = {}
    if stockout_form:
        form_initial['stock_form'] = f"{stockout_form}({former_size})"
        stock_form = f"{stockout_form}({former_size})"

    form = StockDataRecordForm(initial=form_initial)

    is_form_restored = bool(stockout_form)
    show_process_warning = show_noti_modal(request, is_form_restored, action)

    if request.method == 'POST':

        form_name, selected_plant, selected_machine, \
        batch_data_table, basket_data_table, basket_lost_table = handle_stockin_form_input(request)

        if form_name and '(' in form_name and ')' in form_name:
            stockin_form = form_name.split('(')[0].strip()
            former_size = form_name.split('(')[1].split(')')[0].strip()
        else:
            stockin_form = form_name
            former_size = batch_data_table[0]['size'] if batch_data_table else ''

        form_type = request.POST.get('form_type', '').strip()

        if form_type == 'former':
            sql = f"""
                    SELECT 
                        w.stockout_form,
                        w.stockout_total_basket,
                        w.stockout_total_former,
                        w.stockout_return_basket 
                          + ISNULL(SUM(t.rack_total_basket), 0) AS total_return_basket,
                        w.stockout_return_former
                          + ISNULL(SUM(t.rack_total_former), 0) AS total_return_former
                    FROM [GDWMS].[dbo].[wh_former_former_stockout_form] AS w
                    LEFT JOIN [GDWMS].[dbo].[wh_former_former_rack_bin_temp] AS t
                      ON t.stock_form = w.stockout_form
                     AND t.action = 'STIN'
                    WHERE w.stockout_form = '{stockin_form}'
                    GROUP BY 
                        w.stockout_form,
                        w.stockout_total_basket,
                        w.stockout_total_former,
                        w.stockout_return_basket,
                        w.stockout_return_former;

            """
            rows = database().select_sql_dict(sql)

            if basket_data_table:
                sum_basket = len(basket_data_table) #sum(int(item['basket']) for item in basket_data_table)
                if rows:
                    if (int(rows[0]['total_return_basket']) + sum_basket) > int(rows[0]['stockout_total_basket']):
                        error_modal = True
                        error_msg = _('Return quantity is more than out quantity')

                        return render(request, 'wh_former/pages/former_stock_in.html', {**locals()})
                else:
                    if sum_basket > int(rows[0]['stockout_total_basket']):
                        error_modal = True
                        error_msg = _('Return quantity is more than out quantity')

                        return render(request, 'wh_former/pages/former_stock_in.html', {**locals()})

            rack_scanned, total_basket, total_former = Transfer_To_Temps(request, basket_data_table, rfid_reader_ip,
                                                                         client_ip, pid,
                                                                         from_bin=basket_data_table[0]['bin'],
                                                                         to_bin=selected_machine,
                                                                         action=action,
                                                                         stock_form=stockin_form)
            success_modal = True

            if mode != 'init':
                is_form_restored = True

        elif form_type == 'done':
            success, msg = handle_stockout_form_update(stockin_form, former_size, selected_machine, rfid_reader_ip, action)

            if not success:
                error_msg = msg
                error_modal = True

            (batch_no, former_used_day) = msg

            success, error_msg = Transfer_From_Temp(request, rfid_reader_ip, batch_no, action,
                                                    former_used_day, operation_type="stockin",
                                                     stockin_form=stockin_form, stock_form_size=former_size)


            if success:
                success_modal = True
                rack_scanned = total_basket = total_former = 0

                selected_machine = ''
                is_form_restored = False
                stock_form = ''
        elif form_type == 'cancel':
            success, error_msg, total_former, total_basket = Cancel_Operation(request, rfid_reader_ip, action)

            if success:
                success_modal = True
                rack_scanned = error_msg

                stockout_form = request.POST.get('stockout_form', '') or request.GET.get('stockout_form', '')
                if stockout_form:
                    Former_stockout_form.objects.filter(stockout_form=stockout_form).delete()

                is_form_restored = False
                stock_form = ''
            else:
                error_modal = True

    return render(request, 'wh_former/pages/former_stock_in.html', {**locals()})


@login_required
def user_former_stock_in_empty(request):
    mode = request.GET.get('mode', 'init').lower()
    is_wh_former_admin = request.user.groups.filter(name__in=['wh_former_admin', 'developer']).exists()

    result = get_permission(request)
    if isinstance(result, HttpResponse):
        if is_wh_former_admin:
            has_permission_ip = True
        else:
            has_permission_ip = False
            return result
    else:
        has_permission_ip = True


    client_ip, pid, rfid_reader_state, rfid_setting_id, gate_name, rfid_reader_ip, is_ip_allowed = result
    column_width, column_align, column_name = former_master_data_table()
    columns = list(zip(column_name, column_width, column_align))
    locations = RFID_setting.objects.filter(client_device_ip=client_ip).order_by("location_name")

    action = MovementType.objects.get(mvt_code="STIN").mvt_code
    existing_temps = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip,
                                                         action=action).order_by('-rack_scan_order')

    existing_temp = existing_temps.first() if existing_temps.exists() else None
    rack_scanned = existing_temp.rack_scan_order or 0 if existing_temp else 0
    total_basket = existing_temps.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
    total_former = existing_temps.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0

    stockout_data = get_former_stockout_data_as_dict(existing_temp)
    former_size = stockout_data['params_size']
    stockout_form = stockout_data['stockout_form']

    plants, selected_machine, selected_plant = stockin_selection(request)

    if not selected_machine and stockout_data.get('selected_machine'):
        selected_machine = stockout_data['selected_machine']
    if not selected_plant and stockout_data.get('selected_plant'):
        selected_plant = stockout_data['selected_plant']

    form_initial = {}
    if stockout_form:
        form_initial['stock_form'] = f"{stockout_form}({former_size})"
        stock_form = f"{stockout_form}({former_size})"

    form = StockDataRecordForm(initial=form_initial)

    is_form_restored = bool(stockout_form)
    show_process_warning = show_noti_modal(request, is_form_restored, action)

    if request.method == 'POST':

        form_name, selected_plant, selected_machine, \
        batch_data_table, basket_data_table, basket_lost_table = handle_stockin_form_input(request)

        if form_name and '(' in form_name and ')' in form_name:
            stockin_form = form_name.split('(')[0].strip()
            former_size = form_name.split('(')[1].split(')')[0].strip()
        else:
            stockin_form = form_name
            former_size = batch_data_table[0]['size'] if batch_data_table else ''

        form_type = request.POST.get('form_type', '').strip()

        if form_type == 'former':
            # sql = f"""
            #         SELECT
            #             w.stockout_form,
            #             w.stockout_total_basket,
            #             w.stockout_total_former,
            #             w.stockout_return_basket
            #               + ISNULL(SUM(t.rack_total_basket), 0) AS total_return_basket,
            #             w.stockout_return_former
            #               + ISNULL(SUM(t.rack_total_former), 0) AS total_return_former
            #         FROM [GDWMS].[dbo].[wh_former_former_stockout_form] AS w
            #         LEFT JOIN [GDWMS].[dbo].[wh_former_former_rack_bin_temp] AS t
            #           ON t.stock_form = w.stockout_form
            #          AND t.action = 'STIN'
            #         WHERE w.stockout_form = '{stockin_form}'
            #         GROUP BY
            #             w.stockout_form,
            #             w.stockout_total_basket,
            #             w.stockout_total_former,
            #             w.stockout_return_basket,
            #             w.stockout_return_former;
            #
            # """
            # rows = database().select_sql_dict(sql)
            #
            # if basket_data_table:
            #     sum_basket = len(basket_data_table) #sum(int(item['basket']) for item in basket_data_table)
            #     if rows:
            #         if (int(rows[0]['total_return_basket']) + sum_basket) > int(rows[0]['stockout_total_basket']):
            #             error_modal = True
            #             error_msg = _('Return quantity is more than out quantity')
            #
            #             return render(request, 'wh_former/pages/former_stock_in.html', {**locals()})
            #     else:
            #         if sum_basket > int(rows[0]['stockout_total_basket']):
            #             error_modal = True
            #             error_msg = _('Return quantity is more than out quantity')
            #
            #             return render(request, 'wh_former/pages/former_stock_in.html', {**locals()})

            rack_scanned, total_basket, total_former = Transfer_To_Temps(request, basket_data_table, rfid_reader_ip,
                                                                         client_ip, pid,
                                                                         from_bin=basket_data_table[0]['bin'],
                                                                         to_bin=selected_machine,
                                                                         action=action,
                                                                         stock_form=stockin_form)
            success_modal = True

            if mode != 'init':
                is_form_restored = True

        elif form_type == 'done':
            # success, msg = handle_stockout_form_update(stockin_form, former_size, selected_machine, rfid_reader_ip, action)
            #
            # if not success:
            #     error_msg = msg
            #     error_modal = True
            #
            # (batch_no, former_used_day) = msg

            success, error_msg = Transfer_Empty_From_Temp(request, rfid_reader_ip, action)


            if success:
                success_modal = True
                rack_scanned = total_basket = total_former = 0

                selected_machine = ''
                is_form_restored = False
                stock_form = ''
        elif form_type == 'cancel':
            success, error_msg, total_former, total_basket = Cancel_Operation(request, rfid_reader_ip, action)

            if success:
                success_modal = True
                rack_scanned = error_msg

                stockout_form = request.POST.get('stockout_form', '') or request.GET.get('stockout_form', '')
                if stockout_form:
                    Former_stockout_form.objects.filter(stockout_form=stockout_form).delete()

                is_form_restored = False
                stock_form = ''
            else:
                error_modal = True

    return render(request, 'wh_former/pages/former_stock_in_empty.html', {**locals()})


def user_batch_histoty(request):
    current_language = get_language()
    search_batch_no = ''
    data = []
    is_show_batch_no_select = False
    batch_current_total_former = 0
    if request.method == 'POST':
        search_batch_no = request.POST.get('search_batch_no', '').strip()

        where_clause = f"""
                fbdl.batch_no = '{search_batch_no}' 
                OR fbdl.batch_combine = '{search_batch_no}'
            """

    if search_batch_no:
        if current_language == 'en':
            mmt_text_table = '[mvt_name]'
        elif current_language == 'zh-hant':
            mmt_text_table = '[desc]'
        elif current_language == 'vi':
            mmt_text_table = '[mvt_vn_name]'
        else:
            mmt_text_table = '[mvt_name]'

        sql = f"""   
                SELECT 
                    CASE 
                        WHEN fbdl.batch_combine = '{search_batch_no}' THEN ''
                        ELSE fbdl.batch_no
                    END AS batch_no,
                    mmt.{mmt_text_table} AS action_name,
                    CASE 
                        WHEN fbdl.batch_sub_action_name IS NULL THEN ''
                        WHEN fbdl.batch_sub_action_name = 'MERGE' AND 
                             NOT EXISTS (
                                 SELECT 1 
                                 FROM [GDWMS].[dbo].[wh_former_former_batch_data_log] fbdl2 
                                 WHERE fbdl2.batch_sub_action_key = fbdl.batch_sub_action_key 
                                   AND fbdl2.batch_sub_action_name = 'SPLIT'
                             ) THEN ''
                        ELSE fbdl.batch_sub_action_name 
                    END AS batch_sub_action_name,

                    CASE
                        WHEN ISNULL(fbdl.batch_basket_qty_merge, 0) <> 0 THEN
                            CASE 
                                WHEN fbdl.batch_basket_qty_merge > 0 
                                    THEN '+' + CAST(fbdl.batch_basket_qty_merge AS VARCHAR(20))
                                ELSE CAST(fbdl.batch_basket_qty_merge AS VARCHAR(20))
                            END
                        WHEN ISNULL(fbdl.batch_basket_qty_split, 0) <> 0 THEN
                            CASE 
                                WHEN fbdl.batch_basket_qty_split > 0 
                                    THEN '-' + CAST(fbdl.batch_basket_qty_split AS VARCHAR(20))
                                ELSE CAST(fbdl.batch_basket_qty_split AS VARCHAR(20))
                            END
                        ELSE '0'
                    END AS batch_basket_qty_change,

                    fbdl.batch_basket_qty_total,

                    CASE
                        WHEN ISNULL(fbdl.batch_qty_merge, 0) <> 0 THEN
                            CASE 
                                WHEN fbdl.batch_qty_merge > 0 
                                    THEN '+' + CAST(fbdl.batch_qty_merge AS VARCHAR(20))
                                ELSE CAST(fbdl.batch_qty_merge AS VARCHAR(20))
                            END
                        WHEN ISNULL(fbdl.batch_qty_split, 0) <> 0 THEN
                            CASE 
                                WHEN fbdl.batch_qty_split > 0 
                                    THEN '-' + CAST(fbdl.batch_qty_split AS VARCHAR(20))
                                ELSE CAST(fbdl.batch_qty_split AS VARCHAR(20))
                            END
                        ELSE '0'
                    END AS batch_former_qty_change,

                    fbdl.batch_qty_total,
                    fbdl.batch_change_day,
                    fbdl.batch_used_day,
                    fbdl.batch_sub_action_key,

                    -- Gộp stock qty
                    (ISNULL(fbdl.batch_qty_stockout, 0) + ISNULL(fbdl.batch_qty_stockin, 0)) AS batch_qty_stock,

                    -- Gộp stock basket qty
                    (ISNULL(fbdl.batch_basket_qty_stockout, 0) + ISNULL(fbdl.batch_basket_qty_stockin, 0)) AS batch_basket_qty_stock,

                    CASE 
                        WHEN fbdl.batch_combine = '{search_batch_no}'
                        THEN fbdl.batch_no
                        ELSE ''
                    END AS sub_batch_no,
                    fbdl.is_confirmed
                FROM [GDWMS].[dbo].[wh_former_former_batch_data_log] fbdl
                LEFT JOIN [GDWMS].[dbo].[warehouse_movementtype] mmt
                    ON fbdl.batch_action_name = mmt.mvt_code
                WHERE {where_clause}
                ORDER BY 
                    fbdl.batch_sub_action_key,
                    fbdl.batch_change_day,
                    CASE 
                        WHEN fbdl.batch_sub_action_name = 'MERGE' THEN 0
                        WHEN fbdl.batch_sub_action_name = 'SPLIT' THEN 1
                        ELSE 2
                    END;
        """

        try:
            wms_db = database()
            data = wms_db.select_sql_dict(sql)
            from collections import OrderedDict
            
            def _to_int(x, default=0):
                try:
                    if x is None: return default
                    return int(str(x).replace('+', '').strip())
                except Exception:
                    return default

            groups = OrderedDict()
            for r in data:
                key = r.get('batch_sub_action_key')
                if key not in groups:
                    groups[key] = []
                groups[key].append(r)

            new_data = []
            for key, rows in groups.items():
                for row in rows:
                    action_name = row.get('action_name', '').upper()
                    if 'STOCK OUT' in action_name or 'STOU' in action_name or 'XUẤT' in action_name or '出庫' in action_name:
                        row['row_type'] = 'stockout'
                    elif 'STOCK IN' in action_name or 'STIN' in action_name or 'NHẬP' in action_name or '入庫' in action_name:
                        row['row_type'] = 'stockin'
                    elif 'WASHING' in action_name or 'CLEN' in action_name or 'RỬA' in action_name or '乾淨的' in action_name:
                        row['row_type'] = 'washing'
                    elif 'CRTE' in action_name or 'CREATE' in action_name or 'TẠO' in action_name or '創造' in action_name:
                        row['row_type'] = 'create'
                    else:
                        row['row_type'] = 'other'
                
                new_data.extend(rows)

                if key:
                    # Calculate basket stock (Stock IN - Stock OUT)
                    basket_stockin = sum(_to_int(x.get('batch_basket_qty_stock', 0)) for x in rows
                                         if x.get('row_type') == 'stockin')
                    basket_stockout = sum(_to_int(x.get('batch_basket_qty_stock', 0)) for x in rows
                                          if x.get('row_type') == 'stockout')
                    if basket_stockin == 0:
                        basket_stock = 'Not return'
                    else:
                        basket_stock = basket_stockout - basket_stockin


                    former_stockin = sum(_to_int(x.get('batch_qty_stock', 0)) for x in rows
                                         if x.get('row_type') == 'stockin')
                    former_stockout = sum(_to_int(x.get('batch_qty_stock', 0)) for x in rows
                                          if x.get('row_type') == 'stockout')
                    if former_stockin == 0:
                        former_stock = _('Not return')
                    else:
                        former_stock = former_stockout - former_stockin

                    # display_batch_no = next((x.get('batch_no') for x in rows if x.get('batch_no')), '')
                    display_row = next((x for x in rows if x.get('batch_no')), None)
                    if display_row:
                        display_batch_no = display_row.get('batch_no')
                        display_confirmed = display_row.get('is_confirmed')
                        key = display_row.get('batch_sub_action_key')
                        if former_stockin == 0 and former_stockout > 0:
                            display_confirmed = True
                        if former_stockout == 0 and former_stockin > 0:
                            display_confirmed = True

                    else:
                        display_batch_no = ''
                        display_confirmed = None
                        key = ''

                    print(display_confirmed)
                    print(key)

                    new_data.append({
                        'batch_no': display_batch_no,
                        'action_name': 'SUMMARY',
                        'batch_sub_action_name': '------',
                        'batch_basket_qty_change': 'Baskets:',
                        'batch_basket_qty_stock': basket_stock,
                        'batch_basket_qty_total': '',
                        'batch_former_qty_change': 'Formers:',
                        'batch_qty_stock': former_stock,
                        'batch_qty_total': '',
                        'batch_change_day': '------',
                        'batch_used_day': '------',
                        'sub_batch_no': '------',
                        'is_summary': 1,
                        'row_type': 'summary',
                        'is_confirmed': display_confirmed,
                        'is_z_in_batch': True if 'Z' in display_batch_no else False,
                        'key': key
                    })

                data = new_data

            sql1 = f""" SELECT *
                        FROM [GDWMS].[dbo].[wh_former_former_batch_data]
                        where batch_no = '{search_batch_no}'"""
            batch_current_info = wms_db.select_sql_dict(sql1)
            batch_current_total_former = batch_current_info[0]['batch_total_former']


        except Exception as e:
            data = []
            error_msg = f"Database query error: {e}"

    return render(request, 'wh_former/pages/batch_history.html', {
        'search_batch_no': search_batch_no,
        'data': data,
        'isShowBatchNoSelect': is_show_batch_no_select,
        'batch_current_total_former': batch_current_total_former
    })


def user_batch_action_history(request):
    search_batch_no = request.GET.get('batch_no', '').strip()
    all_logs_with_related = []
    total_records = 0

    if search_batch_no:
        batch_logs = Former_batch_data_log.objects.filter(
            batch_no=search_batch_no
        ).order_by('-batch_change_day', '-id')

        stou_merge_split_keys = Former_batch_data_log.objects.filter(
            batch_no=search_batch_no,
            batch_action_name='STOU',
            batch_sub_action_name__in=['MERGE', 'SPLIT'],
            batch_sub_action_key__isnull=False
        ).values_list('batch_sub_action_key', flat=True).distinct()

        merge_split_groups = {}
        if stou_merge_split_keys:
            related_logs = Former_batch_data_log.objects.filter(
                batch_sub_action_key__in=stou_merge_split_keys,
                batch_action_name='STOU',
                batch_sub_action_name__in=['MERGE', 'SPLIT']
            ).exclude(batch_no=search_batch_no).order_by('batch_sub_action_key', 'batch_no')

            for log in related_logs:
                key = log.batch_sub_action_key
                if key not in merge_split_groups:
                    merge_split_groups[key] = []
                merge_split_groups[key].append(log)

        for log in batch_logs:
            log_data = {
                'log': log,
                'related_batches': []
            }

            if (log.batch_sub_action_key and
                    log.batch_sub_action_name in ['MERGE', 'SPLIT'] and
                    log.batch_sub_action_key in merge_split_groups):
                log_data['related_batches'] = merge_split_groups[log.batch_sub_action_key]

            all_logs_with_related.append(log_data)

        total_related = sum(len(batches) for batches in merge_split_groups.values())
        total_records = len(batch_logs) + total_related

    return render(request, 'wh_former/pages/batch_action_history.html', {
        'search_batch_no': search_batch_no,
        'all_logs_with_related': all_logs_with_related,
        'total_records': total_records
    })

@login_required
def former_transaction(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if data.get('action') == 'save_confirmed_amounts':
                try:
                    data = json.loads(request.body)
                    if data.get('action') == 'save_confirmed_amounts':
                        with transaction.atomic():
                            for row_data in data.get('data', []):
                                try:
                                    # Parse the date from "Aug. 11, 2025" format
                                    date_obj = datetime.datetime.strptime(row_data['date'], '%b. %d, %Y')
                                    yymm = date_obj.strftime('%Y%m')  # Formats as "202508"
                                except (ValueError, KeyError):
                                    # Fallback to current month if date parsing fails
                                    yymm = now().strftime('%Y%m')

                                # Update or create with both values
                                scrap_maintain.objects.update_or_create(
                                    stockout_form=row_data['stockout_form'],
                                    batch_no=row_data['batch_no'],
                                    yymm=yymm,
                                    defaults={
                                        'stockout_lack_former': int(row_data['former_confirmed']),
                                        'stockout_lack_basket': int(row_data['basket_confirmed']),
                                        'update_by': request.user,
                                        'update_at': now()
                                    }
                                )

                        return JsonResponse({'success': True})
                except Exception as e:
                    return JsonResponse({'success': False, 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    # Get filter parameters
    month = request.GET.get("month")
    year = request.GET.get("year")
    page_number = request.GET.get('page', 1)

    # Build WHERE clause
    conditions = []
    if month and month.isdigit() and 1 <= int(month) <= 12:
        conditions.append(f"MONTH(stockout_date) = {int(month)}")
    if year and year.isdigit() and int(year) >= 2025:
        conditions.append(f"YEAR(stockout_date) = {int(year)}")

    where_script = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Base SQL query
    sql = f"""SELECT 
            wfsf.stockout_form AS [Stock_Out],
            wfsf.stockout_date AS [Date],
            wfsf.stockout_to AS [Machine],
            '' AS [Line],
            wfsf.batch_no AS [Batch_No],
            wfbd.former_item_no AS [Item_No],
            wfbd.former_vendor AS [Brand],
            wfbd.former_length AS [Former_Length],
            wfbd.former_size AS [Former_Size],
            wfsf.stockout_total_former AS [Former_Stock_Out_Amount],
            wfsf.stockout_return_former AS [Former_Stock_In_Amount],
            wfsf.stockout_total_former - wfsf.stockout_return_former AS [Former_Lack_Amount],
            COALESCE(sm.stockout_lack_former, 0) AS [Former_Confirmed_Lack_Amount],
            wfsf.stockout_total_basket AS [Basket_Stock_Out_Amount],
            wfsf.stockout_return_basket AS [Basket_Stock_In_Amount],
            wfsf.stockout_total_basket - wfsf.stockout_return_basket AS [Basket_Lack_Amount],
            COALESCE(sm.stockout_lack_basket, 0) AS [Basket_Confirmed_Lack_Amount]
        FROM 
            wh_former_former_stockout_form wfsf
        INNER JOIN 
            wh_former_former_batch_data wfbd ON wfbd.batch_no = wfsf.batch_no
        LEFT JOIN 
            scrap_maintain sm ON sm.stockout_form = wfsf.stockout_form AND sm.batch_no = wfsf.batch_no
            AND sm.yymm = FORMAT(wfsf.stockout_date, 'yyyyMM') 
        {where_script}"""

    wms_db = database()
    data = wms_db.select_sql_dict(sql)

    paginator = Paginator(data, 25)
    page_obj = paginator.get_page(page_number)

    context = {
        'data': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'now': now()
    }

    return render(request, "wh_former/pages/scrap_report.html", context)


@login_required()
def scrap_to_excel(request):
    # Get filter parameters
    month = request.GET.get("month")
    year = request.GET.get("year")

    # Build WHERE clause
    conditions = []
    if month and month.isdigit() and 1 <= int(month) <= 12:
        conditions.append(f"MONTH(stockout_date) = {int(month)}")
    if year and year.isdigit() and int(year) >= 2025:
        conditions.append(f"YEAR(stockout_date) = {int(year)}")

    where_script = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Base SQL query
    sql = f"""SELECT 
            wfsf.stockout_form AS [Stock Out],
            wfsf.stockout_to AS [Machine],
            '' AS [Line],
            wfsf.batch_no AS [Batch No],
            wfbd.former_item_no AS [Item No],
            wfbd.former_vendor AS [Brand],
            wfbd.former_length AS [Former Length],
            wfbd.former_size AS [Former Size],
            wfsf.stockout_total_former AS [Former Stock Out Amount],
            wfsf.stockout_return_former AS [Former Stock IN Amount],
            wfsf.stockout_total_former - wfsf.stockout_return_former AS [Former Lack Amount],
            COALESCE(sm.stockout_lack_former, 0) AS [Former Confirmed Lack Amount],
            wfsf.stockout_total_basket AS [Basket Stock Out Amount],
            wfsf.stockout_return_basket AS [Basket Stock IN Amount],
            wfsf.stockout_total_basket - wfsf.stockout_return_basket AS [Basket Lack Amount],
            COALESCE(sm.stockout_lack_basket, 0) AS [Basket Confirmed Lack Amount]
        FROM 
            wh_former_former_stockout_form wfsf
        INNER JOIN 
            wh_former_former_batch_data wfbd ON wfbd.batch_no = wfsf.batch_no
        LEFT JOIN 
            scrap_maintain sm ON sm.stockout_form = wfsf.stockout_form AND sm.batch_no = wfsf.batch_no
            AND sm.yymm = FORMAT(wfsf.stockout_date, 'yyyyMM') 
        {where_script}
        ORDER BY wfsf.stockout_date DESC, wfsf.stockout_form"""

    # Get data from database
    wms_db = database()
    data = wms_db.select_sql_dict(sql)

    # Convert data to proper format for Excel
    excel_data = []
    for row in data:
        excel_data.append({
            "Stock Out": row["Stock Out"],
            "Machine": row["Machine"],
            "Line": row["Line"],
            "Batch No": row["Batch No"],
            "Item No": row["Item No"],
            "Brand": row["Brand"],
            "Former Length": row["Former Length"],
            "Former Size": row["Former Size"],
            "Former Stock Out Amount": row["Former Stock Out Amount"],
            "Former Stock IN Amount": row["Former Stock IN Amount"],
            "Former Lack Amount": row["Former Lack Amount"],
            "Former Confirmed Lack Amount": row["Former Confirmed Lack Amount"],
            "Basket Stock Out Amount": row["Basket Stock Out Amount"],
            "Basket Stock IN Amount": row["Basket Stock IN Amount"],
            "Basket Lack Amount": row["Basket Lack Amount"],
            "Basket Confirmed Lack Amount": row["Basket Confirmed Lack Amount"]
        })

    return JsonResponse(excel_data, safe=False)


@login_required
def basket_broken_reporting(request):
    wms_db = database()
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            basket_nos = data.get("basket_nos", [])

            if not basket_nos:
                return JsonResponse({"error": "No basket numbers provided."}, status=400)

            basket_list = "', '".join(basket_nos)
            update_sql = f"""
                        UPDATE [GDWMS].[dbo].[wh_former_basket_master_data]
                        SET is_active = 3
                        WHERE basket_no IN ('{basket_list}');
                    """
            wms_db.execute_sql(update_sql)

            return JsonResponse({
                "status": "success",
                "message": f"{len(basket_nos)} basket(s) marked as broken successfully."
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    sql = """
        SELECT 
            fbd.basket_no,
            fbd.bin,

            -- 1. Calculate the effective date (current date if to_bin_key is invalid/empty)
            COALESCE(
                TRY_CAST(
                    '20' + SUBSTRING(fbd.to_bin_key, 6, 2) + '-' + 
                    SUBSTRING(fbd.to_bin_key, 8, 2) + '-' + 
                    SUBSTRING(fbd.to_bin_key, 10, 2) 
                AS DATE),
                CAST(GETDATE() AS DATE) 
            ) AS Effective_Date,

            -- 2. Calculate used_days using the effective date
            DATEDIFF(DAY, bmd.basket_receive_date,
                COALESCE(
                    TRY_CAST(
                        '20' + SUBSTRING(fbd.to_bin_key, 6, 2) + '-' + 
                        SUBSTRING(fbd.to_bin_key, 8, 2) + '-' + 
                        SUBSTRING(fbd.to_bin_key, 10, 2) 
                    AS DATE),
                    CAST(GETDATE() AS DATE) 
                )
            ) AS used_days

        FROM [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
        INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
            ON fbd.basket_no = bmd.basket_no

        -- 3. Filter using the effective date
        WHERE fbd.bin LIKE '%NBR%' 
          AND bmd.is_active != 3
          AND DATEDIFF(DAY, 
                COALESCE(
                    TRY_CAST(
                        '20' + SUBSTRING(fbd.to_bin_key, 6, 2) + '-' + 
                        SUBSTRING(fbd.to_bin_key, 8, 2) + '-' + 
                        SUBSTRING(fbd.to_bin_key, 10, 2) 
                    AS DATE),
                    CAST(GETDATE() AS DATE) 
                ),
                GETDATE()) >= 30

        ORDER BY Effective_Date DESC;
    """

    data = wms_db.select_sql_dict(sql)

    return render(request, 'wh_former/pages/basket_broken_reporting.html', locals())


def basket_broken_get_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        basket_no = data.get("basket_no", "").strip()

        if not basket_no or len(basket_no) != 16:
            return JsonResponse({"error": "Invalid basket number"}, status=400)

        sql = f"""
            SELECT TOP(1)
                fbd.basket_no,
                fbd.bin,

                -- Use current date instead of extracting from to_bin_key
                CAST(GETDATE() AS DATE) AS date_from_to_bin_key,

                -- Calculate used_days as difference between today and basket_receive_date
                DATEDIFF(DAY, bmd.basket_receive_date, CAST(GETDATE() AS DATE)) AS used_days

            FROM [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
            INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
                ON fbd.basket_no = bmd.basket_no
            WHERE fbd.basket_no = '{basket_no}'
            ORDER BY date_from_to_bin_key DESC;
        """
        wms_db = database()
        result = wms_db.select_sql_dict(sql)

        if not result:
            return JsonResponse({"error": f"Basket {basket_no} not found."}, status=404)

        record = result[0]
        return JsonResponse({
            "basket_no": record.get("basket_no"),
            "bin": record.get("bin"),
            "date_from_to_bin_key": str(record.get("date_from_to_bin_key")),
            "used_days": record.get("used_days"),
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@login_required
def former_broken_reporting(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        rows = data.get('rows', [])

        if not rows:
            return JsonResponse({"error": "No data received"}, status=400)

        wms_db = database()
        clamped_batches = []  # to store batches whose qty hit 0

        try:
            for row in rows:
                batch_no = row.get('batch_no')
                former = int(row.get('former', 0))
                basket = int(row.get('basket', 0))

                if not batch_no:
                    continue

                # --- Get current quantities ---
                select_sql = f"""
                    SELECT 
                        batch_total_former,
                        batch_total_basket,
                        batch_total_former_in_wh,
                        batch_total_basket_in_wh
                    FROM [GDWMS].[dbo].[wh_former_former_batch_data]
                    WHERE batch_no = '{batch_no}'
                """
                result = wms_db.fetch_one(select_sql)
                if not result:
                    continue

                (
                    batch_total_former,
                    batch_total_basket,
                    batch_total_former_in_wh,
                    batch_total_basket_in_wh
                ) = result

                # --- Calculate new values with clamping ---
                new_former = max(batch_total_former - former, 0)
                new_basket = max(batch_total_basket - basket, 0)
                new_former_wh = max(batch_total_former_in_wh - former, 0)
                new_basket_wh = max(batch_total_basket_in_wh - basket, 0)

                # If any value was clamped, note this batch
                if (
                        new_former == 0 and batch_total_former - former < 0
                ) or (
                        new_basket == 0 and batch_total_basket - basket < 0
                ):
                    clamped_batches.append(batch_no)

                # --- Update wh_former_former_batch_data_log ---
                update_log_sql = f"""
                    UPDATE [GDWMS].[dbo].[wh_former_former_batch_data_log]
                    SET is_confirmed = 1
                    WHERE batch_no = '{batch_no}' AND batch_action_name IN ('STOU', 'STIN')
                """
                wms_db.execute_sql(update_log_sql)

                # --- Update wh_former_former_batch_data ---
                update_batch_sql = f"""
                    UPDATE [GDWMS].[dbo].[wh_former_former_batch_data]
                    SET 
                        batch_total_former = {new_former},
                        batch_total_basket = {new_basket},
                        batch_total_former_in_wh = {new_former_wh},
                        batch_total_basket_in_wh = {new_basket_wh},
                        update_at = GETDATE()
                    WHERE batch_no = '{batch_no}'
                """
                wms_db.execute_sql(update_batch_sql)

            # --- Build response message ---
            if clamped_batches:
                msg = (
                    f"Batch records updated successfully, "
                    f"but some values were clamped to 0 for batches: {', '.join(clamped_batches)}"
                )
            else:
                msg = "Batch records updated successfully."

            return JsonResponse({"message": msg})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # ----- GET REQUEST -----
    column_width, column_align, column_name = former_broken_reporting_table()
    columns = list(zip(column_name, column_width, column_align))

    query_day = 3   # 3 days ago

    sql = f"""
        WITH valid_pairs AS (
            SELECT DISTINCT
                l1.batch_no,
                l1.batch_sub_action_key
            FROM [GDWMS].[dbo].[wh_former_former_batch_data_log] AS l1
            INNER JOIN [GDWMS].[dbo].[wh_former_former_batch_data_log] AS l2
                ON l1.batch_no = l2.batch_no
                AND l1.batch_sub_action_key = l2.batch_sub_action_key
                AND l1.batch_action_name = 'STOU'
                AND l2.batch_action_name = 'STIN'
        ),
        batch_summary AS (
            SELECT 
                l.batch_no,
                -- Former quantity = (sum of stockout - sum of stockin)
                SUM(
                    CASE 
                        WHEN l.batch_action_name = 'STOU' THEN l.batch_qty_stockout
                        WHEN l.batch_action_name = 'STIN' THEN -l.batch_qty_stockin
                        ELSE 0
                    END
                ) AS total_batch_qty,
        
                -- Basket quantity = (sum of basket stockout - sum of basket stockin)
                SUM(
                    CASE 
                        WHEN l.batch_action_name = 'STOU' THEN l.batch_basket_qty_stockout
                        WHEN l.batch_action_name = 'STIN' THEN -l.batch_basket_qty_stockin
                        ELSE 0
                    END
                ) AS total_basket_qty,
        
                -- Sum the used day normally
                SUM(l.batch_used_day) AS total_batch_used_day
            FROM [GDWMS].[dbo].[wh_former_former_batch_data_log] AS l
            INNER JOIN valid_pairs vp
                ON l.batch_no = vp.batch_no
                AND l.batch_sub_action_key = vp.batch_sub_action_key
            WHERE 
                l.batch_action_name IN ('STOU', 'STIN')
                AND l.is_confirmed = 0
                -- Only include items updated exactly 3 days ago
                AND CAST(l.update_at AS DATE) = CAST(DATEADD(DAY, -{query_day}, GETDATE()) AS DATE)
            GROUP BY l.batch_no
        ),
        valid_bins AS (
            SELECT DISTINCT 
                batch_no,
                bin
            FROM [GDWMS].[dbo].[wh_former_former_bin_data]
            WHERE 
                bin NOT LIKE 'NBR%' 
                AND bin NOT LIKE 'Z%'
                AND batch_no IS NOT NULL
        )
        SELECT 
            bs.batch_no,
            vb.bin,
            bs.total_batch_used_day,
            bs.total_batch_qty,
            bs.total_basket_qty
        FROM batch_summary AS bs
        JOIN valid_bins AS vb
            ON bs.batch_no = vb.batch_no
        ORDER BY 
            bs.batch_no;
    """

    wms_db = database()
    results = wms_db.select_sql_dict(sql)
    data = convert_batch_summary_results(results, column_width, column_align)

    return render(request, 'wh_former/pages/former_broken_reporting.html', locals())


def convert_batch_summary_results(results, column_width, column_align):
    formatted_results = []

    for i, row in enumerate(results, start=1):

        row_data = list(zip([
            i,
            row.get('batch_no', ''),
            row.get('bin', ''),
            row.get('total_batch_used_day', 0),
            row.get('total_batch_qty', 0),
            row.get('total_basket_qty', 0),
            '',
        ], column_width, column_align))

        formatted_results.append((row_data, True))

    return formatted_results


