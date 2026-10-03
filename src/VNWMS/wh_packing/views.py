import json
import os

import openpyxl
import pandas as pd
from datetime import datetime

from django.contrib import messages
from django.urls import reverse
from django.utils.translation import get_language
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from VNWMS.database import sap_database, database
from users.models import CustomUser
from warehouse.models import Warehouse, MovementType, Area, ItemType, Plant
from warehouse.utils import get_item_type_name, get_item_type_object, get_type_code_by_desc, get_item_type_from_sap
from wh_packing.forms import BinSearchForm, StockInPForm, StockOutPForm, BinTransferForm, QuantityAdjustForm, \
    ExcelUploadForm, BinValueSearchForm, BinValueDeleteForm, SAPUploadForm, SAPQueryForm, Excel2UploadForm, \
    BatchSearchForm
from wh_packing.utils import inventory_search, inventory_history, Do_Transaction, \
    inventory_id_search
from .models import Bin, Bin_Value, Bin_Value_History, Series, StockInForm, StockOutForm, SAP_Inventory
from django.db.models import Case, When, Value, BooleanField, Q, F, CharField


@login_required
def bin_search(request):
    form = BinSearchForm(request.GET or None, user=request.user)

    if form.is_valid():
        query_plant = form.cleaned_data.get('plant')
        query_bin = form.cleaned_data.get('bin')
        query_po_no = form.cleaned_data.get('po_no')
        query_pu_no = form.cleaned_data.get('pu_no')
        query_size = form.cleaned_data.get('size')
        query_ver_no = form.cleaned_data.get('version_no')
        query_item_type = form.cleaned_data.get('item_type')
        query_from = form.cleaned_data.get('from_date')
        query_to = form.cleaned_data.get('to_date')

        warehouse = Warehouse.objects.filter(wh_plant=query_plant, wh_packing_func=True).first()

        if query_plant:

            bin_hists = inventory_history(warehouse=warehouse, location=query_bin, product_order=query_po_no, purchase_order=query_pu_no,
                                          size=query_size, version_no=query_ver_no,
                                          item_type=get_type_code_by_desc(query_item_type),
                                          from_date=query_from, to_date=query_to)

            bin_values = inventory_search(warehouse=warehouse, location=query_bin, product_order=query_po_no, purchase_order=query_pu_no,
                                          size=query_size, version_no=query_ver_no,
                                          item_type=get_type_code_by_desc(query_item_type))

            result_value = bin_values
            result_history = bin_hists

            total_qty = sum(record['qty'] for record in result_value)

            bin_hists_data = []
            for record in bin_hists:

                item_type = None
                if record.item_type_id:
                    try:
                        item_type = ItemType.objects.get(type_code=record.item_type_id)
                        item_type_name = item_type.get_item_type_name()
                    except ItemType.DoesNotExist:
                        item_type_name = None

                bin_hists_data.append({
                    "id": record.id,
                    "wh_name": record.warehouse.wh_name,
                    "bin_id": record.bin_id,
                    "product_order": record.product_order,
                    "purchase_no": record.purchase_no,
                    "item_type": item_type_name,
                    "size": record.size,
                    "mvt_name": record.mvt.get_translated_name(),
                    "plus_qty": record.plus_qty,
                    "minus_qty": record.minus_qty,
                    "remain_qty": record.remain_qty,
                    "purchase_unit": record.purchase_unit,
                    "comment": record.comment,
                    "create_at": record.create_at,
                    "create_by_username": record.create_by.username,
                })

            return JsonResponse(
                {
                    "bin_hists": bin_hists_data,
                    "bin_values": list(bin_values),
                    "total_qty": total_qty,
                })
        return JsonResponse({"message": "Invalid request."}, status=400)

    return render(request, 'wh_packing/search/bin_history_search.html', locals())


@login_required
def trans_hist_top100(request):
    return render(request, 'wh_packing/search/bin_history_top100_search.html', locals())


def check_po_exists(request):
    po_no = request.POST.get('po_no')
    bin_id = request.POST.get('bin_id')

    if Bin_Value.objects.filter(bin=bin_id, po_no=po_no).exists():
        return JsonResponse({'exists': True})
    else:
        return JsonResponse({'exists': False})


@login_required
def index(request):
    warehouses = Warehouse.objects.all()
    return render(request, 'wh_packing/search/index.html', locals())


@login_required
def dashboard(request):

    return render(request, 'wh_packing/search/dashboard.html', locals())


@login_required
def warehouse_map(request, pk):
    warehouse = Warehouse.objects.get(wh_code__contains='PKG', wh_plant=request.user.plant, wh_packing_func=True)
    bg = warehouse.wh_bg.url if warehouse.wh_bg else None
    print(warehouse)

    return render(request, 'wh_packing/search/warehouse_map.html', locals())


# 入庫作業
@transaction.atomic
@login_required
def packing_material_stock_in(request):

    warehouse_code = 'PKG'

    bins = Bin.objects.filter(area__warehouse__wh_code='PKG').annotate(
        has_stock=Case(
            When(packing_bin_value_bin__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    )

    form = StockInPForm(user=request.user)
    return render(request, 'wh_packing/action/packing_material_stock_in.html', locals())


@login_required
def stockin_form(request, pk):
    return render(request, 'wh_packing/action/stockin_form.html', locals())


def get_product_order_stout(request):
    data_list_stout = []

    if request.method == 'GET':
        product_order = request.GET.get('product_order')
        purchase_no = request.GET.get('purchase_no')

        size = request.GET.get('size')
        lot_no = request.GET.get('lot_no')
        version_no = request.GET.get('version_no')
        item_type = request.GET.get('item_type')

        plant = request.user.plant_id
        warehouse = Warehouse.objects.filter(wh_plant=plant, wh_packing_func=True).first()

        if all(x == '' for x in [product_order, purchase_no, size, lot_no, version_no, item_type]):
            return JsonResponse({"status": "no_change"}, status=200)
        else:
            raws_stout = inventory_search(warehouse=warehouse, product_order=product_order, purchase_order=purchase_no, size=size,
                                          lot_no=lot_no, version_no=version_no, item_type=item_type)
            for raw in raws_stout:
                data_list_stout.append({'product_order': raw['product_order'],
                                        'size': raw['size'],
                                        'qty': int(raw['qty']),
                                        'bin_id': raw['bin_id'],
                                        'purchase_no': raw['purchase_no'],
                                        'version_no': raw['version_no'],
                                        'version_seq': raw['version_seq'],
                                        'purchase_unit': raw['purchase_unit'],
                                        'customer_no': raw['customer_no'],
                                        'supplier': raw['supplier'],
                                        'lot_no': raw['lot_no'],
                                        'purchase_qty': raw['purchase_qty'],
                                        'item_type': raw['item_type'],
                                        'post_date': raw['post_date'],
                                        'sap_mtr_no': raw['sap_mtr_no'],
                                        'desc': raw['desc'],
                                        'id': raw['id']
                                        })

    return JsonResponse({
        "data_list_stout": data_list_stout
    }, safe=False)


def get_purchase_no_stout(request):
    data_list_stout = []
    if request.method == 'GET':
        product_order = request.GET.get('product_order')
        purchase_no = request.GET.get('purchase_no')

        if purchase_no == '':
            return JsonResponse({"status": "no_change"}, status=200)
        else:
            raws_stout = inventory_search(purchase_order=purchase_no, product_order=product_order)
            for raw in raws_stout:
                data_list_stout.append({'product_order': raw['product_order'],
                                        'size': raw['size'],
                                        'qty': int(raw['qty']),
                                        'bin_id': raw['bin_id'],
                                        'purchase_no': raw['purchase_no'],
                                        'version_no': raw['version_no'],
                                        'version_seq': raw['version_seq'],
                                        'purchase_unit': raw['purchase_unit'],
                                        'customer_no': raw['customer_no'],
                                        'supplier': raw['supplier'],
                                        'lot_no': raw['lot_no'],
                                        'purchase_qty': raw['purchase_qty'],
                                        'item_type': raw['item_type'],
                                        'post_date': raw['post_date'],
                                        'sap_mtr_no': raw['sap_mtr_no'],
                                        'desc': raw['desc'],
                                        })

    return JsonResponse({
        "data_list_stout": data_list_stout
    }, safe=False)


def stockin_filter(raws):
    vnwms_db = database()
    data_list = []
    for raw in raws:
        product_order = raw['VBELN']
        purchase_no = raw['EBELN']
        version_no = raw['ZZVERSION']
        version_seq = raw['ZZVERSION_SEQ']
        size = raw['ZSIZE']
        sap_mtr_no = raw['MBLNR']
        order_qty = raw['MENGE']

        sql2 = f"""
        SELECT sum(order_qty) order_qty FROM [wh_packing_stockinform]
        WHERE product_order='{product_order}' and purchase_no='{purchase_no}'
        and version_no='{version_no}' and version_seq='{version_seq}' and size='{size}'
        and sap_mtr_no = '{sap_mtr_no}'
        """
        stocks = vnwms_db.select_sql_dict(sql2)

        if stocks[0]["order_qty"]:
            qty = int(order_qty) - stocks[0]["order_qty"]
        else:
            qty = int(order_qty)

        if qty > 0:
            data_list.append({'product_order': product_order, 'customer_no': '', 'version_no': version_no,
                              'version_seq': version_seq, 'lot_no': raw['LOTNO'], 'item_type': raw['WGBEZ'],
                              'purchase_no': purchase_no, 'purchase_qty': raw['MENGE_PO'],
                              'size': size, 'purchase_unit': raw['MEINS'], 'post_date': raw['BUDAT'],
                              'order_qty': qty, 'supplier': raw['LIFNR'], 'sap_mtr_no': raw['MBLNR']
                              })
    return data_list


def get_product_order_info(request):
    data_list = []
    if request.method == 'GET':
        product_order = request.GET.get('product_order')
        sap_db = sap_database()

        if product_order == '':
            return JsonResponse({"status": "no_change"}, status=200)
        else:
            sql = f"""
            SELECT VBELN, ZZVERSION, ZZVERSION_SEQ, LOTNO, WGBEZ, EBELN, MENGE_PO, ZSIZE, MEINS, BUDAT, MENGE, LIFNR,
            NAME1, MBLNR
            FROM [PMG_SAP].[dbo].[ZMMT4001] WHERE VBELN = '{product_order}'
            """

        raws = sap_db.select_sql_dict(sql)

        get_item_type_from_sap(raws)
        data_list = stockin_filter(raws)

    return JsonResponse(data_list, safe=False)


def get_purchase_no_info(request):
    data_list = []
    if request.method == 'GET':
        purchase_no = request.GET.get('purchase_no')
        db = sap_database()

        if purchase_no == '':
            return JsonResponse({"status": "no_change"}, status=200)
        else:
            sql = f"""
                    SELECT VBELN, ZZVERSION, ZZVERSION_SEQ, LOTNO, WGBEZ, EBELN, MENGE_PO, ZSIZE, MEINS, BUDAT, MENGE,
                    LIFNR, NAME1, MBLNR
                    FROM [PMG_SAP].[dbo].[ZMMT4001] WHERE EBELN = '{purchase_no}'
                    """

        raws = db.select_sql_dict(sql)

        get_item_type_from_sap(raws)
        data_list = stockin_filter(raws)

    return JsonResponse(data_list, safe=False)


def get_series_number(_key, _key_name):
    obj = Series.objects.filter(key=_key)
    if obj:
        _series = obj[0].series + 1
        obj.update(series=_series, desc=_key_name)
    else:
        _series = 1
        Series.objects.create(key=_key, series=1, desc=_key_name)
    return _series


@csrf_exempt
def packing_material_stock_in_post(request):

    if request.method == "POST":
        try:
            # 解析 JSON 資料
            data = json.loads(request.body)

            # STIN-202412310001
            YYYYMM = datetime.now().strftime("%Y%m")
            key = "STIN" + YYYYMM
            form_no = key + str(get_series_number(key, "STOCKIN")).zfill(3)

            mvt = MovementType.objects.get(mvt_code="STIN")

            with transaction.atomic():
                for item in data:
                    bin = Bin.objects.get(bin_id=item['order_bin'])
                    warehouse_id = bin.area.warehouse
                    size = item['size'].upper()

                    if 'order_qty' in item and int(item['order_qty']) <= 0:
                        return JsonResponse(
                            {
                                "status": "fail",
                                "error": {
                                    "field": "order_qty",
                                    "message": _("The quantity must be a positive number!")
                                }

                            },
                            status=400
                        )

                    if 'item_type' in item and item['item_type']:
                        try:
                            item_type = ItemType.objects.get(
                                Q(type_code=item['item_type']) |
                                Q(type_name=item['item_type']) |
                                Q(type_vn_name=item['item_type'])
                            )
                            item['item_type'] = item_type.type_code

                            post_date_raw = item['post_date']
                            post_date = post_date_raw.replace("-", "")

                            stockin_form = StockInForm(
                                form_no=form_no,
                                product_order=item['product_order'],
                                customer_no=item['customer_no'],
                                version_no=item['version_no'],
                                version_seq=item['version_seq'],
                                lot_no=item['lot_no'],
                                item_type=item_type,
                                purchase_no=item['purchase_no'],
                                purchase_qty=int(float(item['purchase_qty'])) if item['purchase_qty'] else 0,
                                size=size,
                                purchase_unit=item['purchase_unit'],
                                post_date=post_date,
                                order_qty=int(float(item['order_qty'])),
                                order_bin=bin,
                                supplier=item['supplier'],
                                sap_mtr_no=item['sap_mtr_no'],
                                desc=item['desc'],
                                create_at=timezone.now(),
                                create_by_id=request.user.id
                            )
                            stockin_form.save()

                            Do_Transaction(request,
                                           form_no, warehouse_id,
                                           item['product_order'], item['purchase_no'], item['version_no'],
                                           item['version_seq'], item_type.type_code, size, mvt, bin, item['order_qty'],
                                           item['purchase_unit'], item['desc'], stockin_form=form_no)

                        except Exception as e:
                            raise ValueError(f"{e}")
                            print(e)

                return JsonResponse({'status': 'success'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': _('Invalid request method')}, status=405)


# @transaction.atomic
@login_required
def packing_material_stock_out(request):
    if request.method == 'POST':
        form = StockOutPForm(request.POST)
    else:
        form = StockOutPForm()
    return render(request, 'wh_packing/action/packing_material_stock_out.html', {'form': form})


@csrf_exempt
@login_required
def packing_material_stock_out_post(request):
    if request.method == "POST":
        try:
            # 解析 JSON 資料
            data = json.loads(request.body)
            ids_to_stou = data.get("ids", [])

            # STIN-202412310001
            YYYYMM = datetime.now().strftime("%Y%m")
            key = "STOU" + YYYYMM
            form_no = key + str(get_series_number(key, "STOCKOUT")).zfill(3)

            mvt = MovementType.objects.get(mvt_code="STOU")

            for item in data["list_data"]:
                bin = Bin.objects.get(bin_id=item['binId'])
                warehouse_id = bin.area.warehouse
                comment = item['desc'] if 'desc' in item else ""
                type_name = item['itemType']
                item_type = ItemType.objects.get(
                    Q(type_code=type_name) |
                    Q(type_name=type_name) |
                    Q(type_vn_name=type_name)
                )

                try:

                    stockout_form = StockOutForm(
                        form_no=form_no,
                        product_order=item['productOrder'],
                        version_no=item['versionNo'],
                        version_seq=item['versionSeq'],
                        purchase_no=item['purchaseNo'],
                        item_type=item_type,
                        size=item['size'],
                        purchase_unit=item['purchaseUnit'],
                        order_bin=bin,
                        desc=comment,
                        create_at=timezone.now(),
                        create_by_id=request.user.id
                    )
                    stockout_form.save()

                    qty = int(item['qty']) * -1

                    result = Do_Transaction(request, form_no, warehouse_id, item['productOrder'],
                                            item['purchaseNo'],
                                            item['versionNo'],
                                            item['versionSeq'],
                                            item_type.type_code,
                                            item['size'], mvt,
                                            item['binId'], qty,
                                            item['purchaseUnit'],
                                            comment,
                                            stockout_form=form_no)

                except Exception as e:
                    raise ValueError(f"{e}")
                    print(e)
            if not ids_to_stou:
                return JsonResponse({"success": False, "error": "Không có dữ liệu để xóa!"})
            return JsonResponse({'status': 'success'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required
def product_order_search(request):
    product_order = request.GET.get('product_order')
    size = request.GET.get('size')

    warehouse = Warehouse.objects.filter(wh_plant=request.user.plant, wh_packing_func=True).values_list('wh_code', flat=True).first()

    if not product_order and not size:
        return JsonResponse({"status": "blank"}, status=200)

    request.session['search_results_url'] = request.get_full_path()
    if product_order or size:

        # item_type_column = get_item_type_name()

        bin_values = inventory_search(warehouse=warehouse, product_order=product_order, size=size)

        data = list(bin_values)

        if not data:
            return JsonResponse({"status": "blank"}, status=200)

    return JsonResponse(data, safe=False)


@login_required
def transfer_and_adjust(request):
    return render(request, 'wh_packing/action/packing_transfer_and_adjust.html')


# no use this
@login_required
def bin_transfer(request):
    if request.GET:
        request.session['wh_name'] = request.GET.get('wh_name', '')
        request.session['product_order'] = request.GET.get('product_order', '')
        request.session['purchase_no'] = request.GET.get('purchase_no', '')
        request.session['version_no'] = request.GET.get('version_no', '')
        request.session['version_seq'] = request.GET.get('version_seq', '')
        request.session['item_type'] = request.GET.get('item_type', '')
        request.session['lot_no'] = request.GET.get('lot_no', '')
        request.session['size'] = request.GET.get('size', '')
        request.session['bin_id'] = request.GET.get('bin_id', '')
        request.session['qty'] = request.GET.get('qty', '')
        request.session['purchase_unit'] = request.GET.get('purchase_unit', '')
        request.session['customer_no'] = request.GET.get('customer_no', '')
        request.session['purchase_qty'] = request.GET.get('purchase_qty', '')
        request.session['post_date'] = request.GET.get('post_date', '')
        request.session['sap_mtr_no'] = request.GET.get('sap_mtr_no', '')
        request.session['supplier'] = request.GET.get('supplier', '')
        request.session['desc'] = request.GET.get('desc', '')

    wh_name = request.session.get('wh_name', '')
    product_order = request.session.get('product_order', '')
    purchase_no = request.session.get('purchase_no', '')
    version_no = request.session.get('version_no', '')
    version_seq = request.session.get('version_seq', '')
    item_type = request.session.get('item_type', '')
    lot_no = request.session.get('lot_no', '')
    size = request.session.get('size', '')
    bin_id = request.session.get('bin_id', '')
    qty = request.session.get('qty', '')

    item_data = {
        'wh_name': wh_name,
        'product_order': product_order,
        'purchase_no': purchase_no,
        'version_no': version_no,
        'version_seq': version_seq,
        'item_type': item_type,
        'lot_no': lot_no,
        'size': size,
        'bin_id': bin_id,
        'qty': qty
    }
    print("item_data: ", item_data)

    return JsonResponse(item_data, safe=False)


# When click 'Transfer' button, execute this one
@login_required
def bin_transfer_page(request):

    if request.method == 'GET':
        request.session['wh_name'] = request.GET.get('wh_name', '')
        request.session['product_order'] = request.GET.get('product_order', '')
        request.session['purchase_no'] = request.GET.get('purchase_no', '')
        request.session['version_no'] = request.GET.get('version_no', '')
        request.session['version_seq'] = request.GET.get('version_seq', '')
        request.session['item_type'] = request.GET.get('item_type', '')
        request.session['lot_no'] = request.GET.get('lot_no', '')
        request.session['size'] = request.GET.get('size', '')
        request.session['bin_id'] = request.GET.get('bin_id', '')
        request.session['qty'] = request.GET.get('qty', '')
        request.session['purchase_unit'] = request.GET.get('purchase_unit', '')
        request.session['customer_no'] = request.GET.get('customer_no', '')
        request.session['purchase_qty'] = request.GET.get('purchase_qty', '')
        request.session['post_date'] = request.GET.get('post_date', '')
        request.session['sap_mtr_no'] = request.GET.get('sap_mtr_no', '')
        request.session['supplier'] = request.GET.get('supplier', '')
        request.session['desc'] = request.GET.get('desc', '')

    wh_name = request.session.get('wh_name', '')
    warehouse = Warehouse.objects.filter(wh_name=wh_name).first()
    product_order = request.session.get('product_order', '')
    purchase_no = request.session.get('purchase_no', '')
    version_no = request.session.get('version_no', '')
    version_seq = request.session.get('version_seq', '')
    item_type = request.session.get('item_type', '')
    lot_no = request.session.get('lot_no', '')
    size = request.session.get('size', '')
    bin_id = request.session.get('bin_id', '')
    qty = request.session.get('qty', '')
    purchase_unit = request.session.get('purchase_unit', '')
    customer_no = request.session.get('customer_no', '')
    purchase_qty = request.session.get('purchase_qty', '')
    post_date = request.session.get('post_date', '')
    sap_mtr_no = request.session.get('sap_mtr_no', '')
    supplier = request.session.get('supplier', '')
    desc = request.session.get('desc', '')

    if request.method == 'POST':
        form = BinTransferForm(request.POST, user=request.user)

        mvt = MovementType.objects.get(mvt_code="TRNS")
        YYYYMM = datetime.now().strftime("%Y%m")

        # key = "TRNS" + YYYYMM
        # form_no = key + str(get_series_number(key, "TRANSFER")).zfill(3)

        key_stin = "STIN" + YYYYMM
        key_stou = "STOU" + YYYYMM
        stockin_form = key_stin + str(get_series_number(key_stin, "STOCKIN")).zfill(3)
        stockout_form = key_stou + str(get_series_number(key_stou, "STOCKOUT")).zfill(3)

        if form.is_valid():
            bin_selected = form.cleaned_data['bin']
            qty = form.cleaned_data['qty']
            type_code = get_item_type_object(item_type).type_code

            new_bin_obj = Bin.objects.filter(bin_id=bin_selected).first()
            old_bin_obj = Bin.objects.filter(bin_id=bin_id).first()

            # inv = Bin_Value.objects.get(warehouse=warehouse, product_order=product_order,purchase_no=purchase_no,
            #                             version_no=version_no,version_seq=version_seq,size=size,bin_id=bin_id, item_type=type_code)
            # stockin_form = inv.stockin_form
            # stockout_status = inv.stockout_form

            trans_item = ItemType.objects.get(
                Q(type_code=item_type) |
                Q(type_name=item_type) |
                Q(type_vn_name=item_type)
            )

            with transaction.atomic():
                stockout_action = StockOutForm(
                    form_no=stockout_form,
                    product_order=product_order,
                    version_no=version_no,
                    version_seq=version_seq,
                    purchase_no=purchase_no,
                    item_type=trans_item,
                    size=size,
                    purchase_unit=purchase_unit,
                    order_bin=old_bin_obj,
                    desc=desc,
                    create_at=timezone.now(),
                    create_by_id=request.user.id
                )
                stockout_action.save()

                stockin_action = StockInForm(
                    form_no=stockin_form,
                    product_order=product_order,
                    customer_no=customer_no,
                    version_no=version_no,
                    version_seq=version_seq,
                    lot_no=lot_no,
                    item_type=trans_item,
                    purchase_no=purchase_no,
                    purchase_qty=int(purchase_qty),
                    size=size,
                    purchase_unit=purchase_unit,
                    post_date=post_date,
                    order_qty=int(qty),
                    order_bin=new_bin_obj,
                    supplier=supplier,
                    sap_mtr_no=sap_mtr_no,
                    desc=desc,
                    create_at=timezone.now(),
                    create_by_id=request.user.id
                )
                stockin_action.save()

                Do_Transaction(request, stockin_form, warehouse, product_order, purchase_no, version_no, version_seq, type_code, size, mvt,
                               bin_selected, qty, purchase_unit, stockin_form=stockin_form, desc=None)
                Do_Transaction(request, stockout_form, warehouse, product_order, purchase_no, version_no, version_seq, type_code, size, mvt,
                               bin_id, -qty, purchase_unit, stockout_form=stockout_form, desc=None)

                item_data = {
                    'wh_name': wh_name,
                    'product_order': product_order,
                    'purchase_no': purchase_no,
                    'version_no': version_no,
                    'version_seq': version_seq,
                    'item_type': type_code,
                    'lot_no': lot_no,
                    'size': size,
                    'bin_id': bin_id,
                    'qty': qty
                }
                return render(request, 'wh_packing/action/packing_transfer_and_adjust.html', locals())
    form = BinTransferForm(user=request.user)

    return render(request, 'wh_packing/action/packing_bin_transfer.html', locals())


@login_required
def bin_adjust(request):
    if request.GET:
        request.session['wh_name'] = request.GET.get('wh_name', '')
        request.session['product_order'] = request.GET.get('product_order', '')
        request.session['purchase_no'] = request.GET.get('purchase_no', '')
        request.session['version_no'] = request.GET.get('version_no', '')
        request.session['version_seq'] = request.GET.get('version_seq', '')
        request.session['item_type'] = request.GET.get('item_type', '')
        request.session['lot_no'] = request.GET.get('lot_no', '')
        request.session['size'] = request.GET.get('size', '')
        request.session['bin_id'] = request.GET.get('bin_id', '')
        request.session['qty'] = request.GET.get('qty', '')
        request.session['customer_no'] = request.GET.get('customer_no', '')
        request.session['purchase_qty'] = request.GET.get('purchase_qty', '')
        request.session['post_date'] = request.GET.get('post_date', '')
        request.session['sap_mtr_no'] = request.GET.get('sap_mtr_no', '')
        request.session['supplier'] = request.GET.get('supplier', '')
        request.session['desc'] = request.GET.get('desc', '')

    wh_name = request.session.get('wh_name', '')
    product_order = request.session.get('product_order', '')
    purchase_no = request.session.get('purchase_no', '')
    version_no = request.session.get('version_no', '')
    version_seq = request.session.get('version_seq', '')
    item_type = request.session.get('item_type', '')
    lot_no = request.session.get('lot_no', '')
    size = request.session.get('size', '')
    bin_id = request.session.get('bin_id', '')
    qty = request.session.get('qty', '')

    item_data = {
        'wh_name': wh_name,
        'product_order': product_order,
        'purchase_no': purchase_no,
        'version_no': version_no,
        'version_seq': version_seq,
        'item_type': item_type,
        'lot_no': lot_no,
        'size': size,
        'bin_id': bin_id,
        'qty': qty
    }

    return JsonResponse(item_data, safe=False)


# When click 'Transfer' button, execute this one
@login_required
def bin_adjust_page(request):
    if request.method == 'GET':
        request.session['wh_name'] = request.GET.get('wh_name', '')
        request.session['product_order'] = request.GET.get('product_order', '')
        request.session['purchase_no'] = request.GET.get('purchase_no', '')
        request.session['version_no'] = request.GET.get('version_no', '')
        request.session['version_seq'] = request.GET.get('version_seq', '')
        request.session['item_type'] = request.GET.get('item_type', '')
        request.session['lot_no'] = request.GET.get('lot_no', '')
        request.session['size'] = request.GET.get('size', '')
        request.session['bin_id'] = request.GET.get('bin_id', '')
        request.session['qty'] = request.GET.get('qty', '')
        request.session['purchase_unit'] = request.GET.get('purchase_unit', '')
        request.session['customer_no'] = request.GET.get('customer_no', '')
        request.session['purchase_qty'] = request.GET.get('purchase_qty', '')
        request.session['post_date'] = request.GET.get('post_date', '')
        request.session['sap_mtr_no'] = request.GET.get('sap_mtr_no', '')
        request.session['supplier'] = request.GET.get('supplier', '')
        request.session['desc'] = request.GET.get('desc', '')

        # Lấy dữ liệu từ session nếu không có GET request
    wh_name = request.session.get('wh_name', '')
    warehouse = Warehouse.objects.filter(wh_name=wh_name).first()
    warehouse_id = warehouse
    product_order = request.session.get('product_order', '')
    purchase_no = request.session.get('purchase_no', '')
    version_no = request.session.get('version_no', '')
    version_seq = request.session.get('version_seq', '')
    item_type = request.session.get('item_type', '')
    lot_no = request.session.get('lot_no', '')
    size = request.session.get('size', '')
    bin_id = request.session.get('bin_id', '')
    qty_a = request.session.get('qty', '')
    purchase_unit = request.session.get('purchase_unit', '')
    customer_no = request.session.get('customer_no', '')
    purchase_qty = request.session.get('purchase_qty', '')
    post_date = request.session.get('post_date', '')
    sap_mtr_no = request.session.get('sap_mtr_no', '')
    supplier = request.session.get('supplier', '')
    desc = request.session.get('desc', '')

    mvt = MovementType.objects.get(mvt_code="ADJS")

    YYYYMM = datetime.now().strftime("%Y%m")
    key = "ADJS" + YYYYMM
    form_no = key + str(get_series_number(key, "ADJUST")).zfill(3)

    if request.method == 'POST':
        form = QuantityAdjustForm(request.POST)
        if form.is_valid():
            qty_b = int(form.cleaned_data['qty']) - int(qty_a)

            type_code = get_item_type_object(item_type).type_code

            trans_item = ItemType.objects.get(
                Q(type_code=item_type) |
                Q(type_name=item_type) |
                Q(type_vn_name=item_type)
            )

            order_bin = Bin.objects.filter(bin_id=bin_id).first()

            with transaction.atomic():

                stockin_action = StockInForm(
                    form_no=form_no,
                    product_order=product_order,
                    customer_no=customer_no,
                    version_no=version_no,
                    version_seq=version_seq,
                    lot_no=lot_no,
                    item_type=trans_item,
                    purchase_no=purchase_no,
                    purchase_qty=int(purchase_qty) if purchase_qty else 0,
                    size=size,
                    purchase_unit=purchase_unit,
                    post_date=post_date,
                    order_qty=int(form.cleaned_data['qty']),
                    order_bin=order_bin,
                    supplier=supplier,
                    sap_mtr_no=sap_mtr_no,
                    desc=desc,
                    create_at=timezone.now(),
                    create_by_id=request.user.id
                )
                stockin_action.save()

                Do_Transaction(request, form_no, warehouse_id, product_order, purchase_no, version_no, version_seq, type_code, size, mvt,
                               bin_id, qty_b, purchase_unit, desc=None, stockin_form=form_no)

                item_data = {
                    'wh_name': wh_name,
                    'product_order': product_order,
                    'purchase_no': purchase_no,
                    'version_no': version_no,
                    'version_seq': version_seq,
                    'item_type': type_code,
                    'lot_no': lot_no,
                    'size': size,
                    'bin_id': bin_id,
                    'qty': qty_a
                }
                print(item_data)
                return render(request, 'wh_packing/action/packing_transfer_and_adjust.html', locals())
    form = QuantityAdjustForm()

    return render(request, 'wh_packing/action/packing_bin_adjust.html', locals())


@login_required
def product_order_hist_data(request):
    current_path = request.path
    plant = request.GET.get('plant')

    warehouse = Warehouse.objects.filter(wh_plant=plant, wh_packing_func=True).first()

    product_order = request.GET.get('product_order')
    bin_id = request.GET.get('bin_id')
    size = request.GET.get('size')
    comment = request.GET.get('comment')

    current_language = get_language()
    if current_language == "zh-hant":
        _mvt = 'mvt__desc'
    elif current_language == "vi":
        _mvt = 'mvt__mvt_vn_name'
    else:
        _mvt = 'mvt_id'

    item_type_column = get_item_type_name()

    bin_values = Bin_Value_History.objects.filter(
        (Q(warehouse=warehouse) if warehouse else Q()) &
        (Q(product_order__icontains=product_order) if product_order else Q()) &
        (Q(bin__bin_id__icontains=bin_id) if bin_id else Q()) &
        (Q(size__icontains=size) if size else Q()) &
        (Q(comment__icontains=comment) if comment else Q())
    ).annotate(
        item_type_display=F(f'item_type__{item_type_column}')
    ).values(
        'batch_no',
        'warehouse',
        'warehouse__wh_plant',
        'product_order',
        'purchase_no',
        'version_no',
        'version_seq',
        'item_type_display',
        'size',
        'comment',
        _mvt,
        'bin__bin_name',
        'plus_qty',
        'minus_qty',
        'remain_qty',
        'create_at',
        'create_by__username'
    )
    # total = None
    if current_path == reverse('product_order_hist100_data'):
        # page = int(request.GET.get("pageIndex", 1))
        # size_ = int(request.GET.get("pageSize", 20))
        # start = (page - 1) * size_
        # end = start + size_

        bin_values = bin_values.order_by('-create_at')[:300]
        # total = bin_values.count()
        #
        # bin_values = bin_values[start:end]

    data = [
        {
            "batch_no": item["batch_no"],
            "warehouse_name": item["warehouse__wh_plant"],
            "product_order": item["product_order"],
            "purchase_no": item["purchase_no"],
            "version_no": item["version_no"],
            "version_seq": item["version_seq"],
            "item_type": item["item_type_display"],
            "size": item["size"],
            "comment": item["comment"],
            "mvt_id": item[_mvt],
            "bin_id": item["bin__bin_name"],
            "plus_qty": item["plus_qty"],
            "minus_qty": item["minus_qty"],
            "remain_qty": item["remain_qty"],
            "create_at": item["create_at"].strftime("%d/%m/%Y %H:%M") if isinstance(item["create_at"], datetime) else
            item["create_at"],
            "create_by__username": item["create_by__username"]
        }
        for item in bin_values
    ]

    if not data:
        return JsonResponse({"status": "blank"}, status=200)

    return JsonResponse(data, safe=False)


# EXCEL_IMPORT
@login_required
def product_order_bin_search(request):
    plants = Plant.objects.values('plant_code', 'plant_name')
    return render(request, 'wh_packing/search/product_order_bin_search.html', {'plants': plants})


def to_int_or_none(value):
    """Chuyển đổi giá trị thành int nếu không phải NaN, ngược lại trả về None"""
    return int(value) if pd.notna(value) else None


def to_string_or_none(value):
    return "" if pd.isna(value) else value


def warehouse_sheet(df, request):
    try:
        for _, row in df.iterrows():
            plant_code = to_string_or_none(row["Plant Code"])
            wh_code = to_string_or_none(row["Warehouse Code"])
            wh_name = to_string_or_none(row["Warehouse Name"])
            wh_comment = to_string_or_none(row["Warehouse Comment"])

            created = Warehouse.objects.get_or_create(
                wh_plant=plant_code,
                wh_code=wh_code,
                defaults={
                    'wh_name': wh_name,
                    'wh_comment': wh_comment,
                    'create_at': timezone.now(),
                    'create_by_id': request.user.id,
                    'update_at': timezone.now(),
                    'update_by': request.user
                }
            )
            if not created[1]:
                Warehouse.objects.filter(wh_plant=plant_code, wh_code=wh_code).update(
                    wh_name=wh_name,
                    wh_comment=wh_comment,
                    update_at=timezone.now(),
                    update_by=request.user
                )
    except Exception as e:
        print(e)


def area_sheet(df, request):
    try:
        for _, row in df.iterrows():
            warehouse = to_string_or_none(row["Warehouse Code"])
            area_id = to_string_or_none(row["Area Id"])
            area_name = to_string_or_none(row["Area Name"])
            pos_x = to_string_or_none(row["Position X"])
            pos_y = to_string_or_none(row["Position Y"])
            layer = to_string_or_none(row["Layer"])
            area_w = to_string_or_none(row["Area Width"])
            area_l = to_string_or_none(row["Area Length"])

            wh_object = Warehouse.objects.filter(wh_code=warehouse).first()

            created = Area.objects.get_or_create(
                warehouse=wh_object,
                area_id=area_id,
                defaults={
                    'area_name': area_name,
                    'pos_x': pos_x,
                    'pos_y': pos_y,
                    'layer': layer,
                    'area_w': area_w,
                    'area_l': area_l,
                    'create_at': timezone.now(),
                    # 'create_by_id': request.user.id,
                    'create_by': request.user,
                    'update_at': timezone.now(),
                    'update_by': request.user
                }
            )
            if not created:
                Area.objects.filter(warehouse=wh_object, area_id=area_id).update(
                    area_name=area_name,
                    pos_x=pos_x,
                    pos_y=pos_y,
                    layer=layer,
                    area_w=area_w,
                    area_l=area_l,
                    update_at=timezone.now(),
                    update_by=request.user
                )
    except Exception as e:
        print(e)


def bin_sheet(df, request):
    try:
        for _, row in df.iterrows():
            wh_code = to_string_or_none(row["Warehouse Code"])  # Sửa lại cột
            area_id = to_string_or_none(row["Area Code"])  # Sửa lại cột
            bin_id = to_string_or_none(row["Bin Id"])
            bin_name = to_string_or_none(row["Bin Name"])

            # 1. Tìm Warehouse theo mã wh_code
            warehouse = Warehouse.objects.filter(wh_code=wh_code).first()
            if warehouse is None:
                print(f"ERROR: Warehouse not found {wh_code}")
                continue  # Bỏ qua nếu không tìm thấy

            # 2. Tìm hoặc tạo Area theo warehouse
            area, _ = Area.objects.get_or_create(
                area_id=area_id,
                warehouse=warehouse,  # Gán Warehouse
                defaults={
                    'area_name': area_id,  # Không có "Area Name" nên gán tạm bằng ID
                    'create_at': timezone.now(),
                    'create_by': request.user,
                    'update_at': timezone.now(),
                    'update_by': request.user
                }
            )

            # 3. Kiểm tra Bin đã tồn tại chưa
            existing_bin = Bin.objects.filter(bin_id=bin_id, area=area).first()
            if existing_bin:
                print(f"Bin {bin_id} already exists, ignore!")
                continue  # Không tạo lại nếu đã tồn tại

            # 4. Tạo Bin
            if existing_bin:
                created = Bin.objects.create(
                    bin_id=existing_bin,
                    bin_name=bin_name,
                    area=area,  # Gán Area vào Bin
                    create_at=timezone.now(),
                    create_by=request.user,
                    update_at=timezone.now(),
                    update_by=request.user
                )
            else:
                created = Bin.objects.create(
                    bin_id=bin_id,
                    bin_name=bin_name,
                    area=area,  # Gán Area vào Bin
                    create_at=timezone.now(),
                    create_by=request.user,
                    update_at=timezone.now(),
                    update_by=request.user
                )
            if not created:
                Warehouse.objects.filter(bin_id=bin_id, area=area).update(
                    bin_name=bin_name,
                    update_at=timezone.now(),
                    update_by=request.user
                )
    except Exception as e:
        print(e)


WAB_PROCESSORS = {
    "Warehouse": warehouse_sheet,
    "Area": area_sheet,
    "Location": bin_sheet,
}


@login_required
def import_excel_data(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["file"]
            df_dict = pd.read_excel(excel_file, sheet_name=None)  # Đọc tất cả các sheet

            with transaction.atomic():
                for sheet_name, df in df_dict.items():
                    process_function = WAB_PROCESSORS.get(sheet_name)
                    if process_function:
                        process_function(df, request)  # Gọi function tương ứng

            return render(request, "wh_packing/admin/bin_upload.html",
                          {"form": form, "message": "Upload successfully!"})

    else:
        form = ExcelUploadForm()

    return render(request, "wh_packing/admin/bin_upload.html", locals())


@login_required
def open_data_import(request):
    if request.method == "POST":
        form = Excel2UploadForm(request.POST, request.FILES)
        if form.is_valid():

            excel_file = request.FILES["file"]
            df = pd.read_excel(excel_file, dtype=str)  # Đọc tất cả các sheet, ép kiểu về str
            df.fillna("", inplace=True) # 避免 NaN 值

            valid_bins = set(Bin.objects.values_list("bin_name", flat=True))

            valid_data = df[df["Location"].isin(valid_bins)]
            invalid_data = df[~df["Location"].isin(valid_bins)]

            valid_records = valid_data.to_dict(orient="records")
            invalid_records = invalid_data.to_dict(orient="records")

            for row in valid_records:
                print(row['Location'])

            request.session["valid_data"] = valid_records
            request.session["invalid_data"] = invalid_records

            return render(request, "wh_packing/admin/open_data_import.html", locals())
    else:
        form = Excel2UploadForm()

    return render(request, "wh_packing/admin/open_data_import.html", {"form": form})


def open_data_import_api(request):
    if request.method == "POST" and request.FILES.get("file"):
        form = Excel2UploadForm(request.POST, request.FILES)
        warehouse = request.POST.get('file_type')
        warehouse = Warehouse.objects.get(pk=warehouse)

        if form.is_valid():

            excel_file = request.FILES["file"]
            df = pd.read_excel(excel_file, dtype=str)  # Đọc tất cả các sheet, ép kiểu về str
            df.fillna("", inplace=True) # 避免 NaN 值
            df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce")
            df = df.groupby(
                [
                    "CustomerName",
                    "ProductOrder",
                    "PackingVersion",
                    "Lot",
                    "ItemType",
                    "Size",
                    "StockInDate",
                    "Location",
                    "Supplier",
                    "PurchaseOrder",
                    "TransactionNo"
                ], as_index=False)["Qty"].sum()

            valid_bins = set(Bin.objects.filter(area__warehouse=warehouse).values_list("bin_name", flat=True))
            valid_types = set(ItemType.objects.values_list("type_name", flat=True))

            valid_data = df[df["Location"].isin(valid_bins) & df["ItemType"].isin(valid_types)]

            # 找出 Location 和 Type 同時錯誤的資料
            invalid_data = df[~df.index.isin(valid_data.index)]  # 這裡包含所有不符合條件的資料

            valid_records = valid_data.to_dict(orient="records")
            invalid_records = invalid_data.to_dict(orient="records")

            request.session["valid_data"] = valid_data.to_dict(orient="records")
            request.session["excel_file"] = excel_file
            request.session["warehouse"] = warehouse.pk

            return JsonResponse({
                "valid_data": valid_records,
                "invalid_data": invalid_records
            })

    return JsonResponse({"error": "Invalid request"}, status=400)


def open_data_import_confirm_api(request):
    if request.method == "POST":
        try:
            valid_data = request.session.get("valid_data", [])
            excel_file = request.session.get("excel_file", "")
            warehouse = request.session.get("warehouse", "")
            warehouse = Warehouse.objects.get(pk=warehouse)

            if not valid_data:
                return JsonResponse({"error": "沒有可匯入的數據"}, status=400)

            with transaction.atomic():

                Bin_Value_History.objects.filter(bin__area__warehouse=warehouse).all().delete()
                Bin_Value.objects.filter(bin__area__warehouse=warehouse).all().delete()

                YYYYMM = datetime.now().strftime("%Y%m")
                key = "OPEN" + YYYYMM
                form_no = key + str(get_series_number(key, "OPEN")).zfill(3)

                mvt = MovementType.objects.get(mvt_code="OPEN")

                for row in valid_data:
                    productOrder = row['ProductOrder']
                    purchaseOrder = row['PurchaseOrder']
                    packingVersion = row['PackingVersion']
                    packingSeq = ""
                    size = row['Size']
                    location = row['Location']
                    supplier = row['Supplier']
                    customer = row['CustomerName']
                    stockInDate = row['StockInDate']
                    qty = row['Qty']
                    transactionNo = row['TransactionNo']
                    lot_no = row['Lot']
                    unit = ""
                    item_type = ItemType.objects.get(type_name=row['ItemType'])
                    location = Bin.objects.get(bin_name=location, area__warehouse=warehouse)

                    stockin_form = StockInForm(
                        warehouse=warehouse,
                        form_no=form_no,
                        product_order=productOrder,
                        customer_no=customer,
                        version_no=packingVersion,
                        version_seq=packingSeq,
                        lot_no=lot_no,
                        item_type=item_type,
                        purchase_no=purchaseOrder,
                        size=size,
                        post_date=stockInDate,
                        order_qty=qty,
                        order_bin=location,
                        supplier=supplier,
                        sap_mtr_no=transactionNo,
                        create_at=timezone.now(),
                        create_by_id=request.user.id
                    )
                    stockin_form.save()

                    Do_Transaction(request, form_no, warehouse, productOrder, purchaseOrder,
                                   packingVersion, packingSeq, item_type.type_code, size, mvt, location.bin_id,
                                   qty, unit, desc="", stockin_form=form_no)

                # if hasattr(excel_file, 'temporary_file_path'):
                #     os.remove(excel_file.temporary_file_path())

                del request.session["valid_data"]
                del request.session["excel_file"]

                return JsonResponse({"message": "成功匯入 {} 筆資料".format(len(valid_data))})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "請使用 POST 方法"}, status=400)


@login_required
def sap_import(request):
    if request.method == 'POST':

        form = SAPUploadForm(request.POST, request.FILES)
        if form.is_valid():
            month = request.POST.get('month')
            plant = request.POST.get('plant')
            sap_file = request.FILES['file']
            wb = openpyxl.load_workbook(sap_file)
            ws = wb.active

            try:
                with transaction.atomic():
                    warehouse = Warehouse.objects.filter(wh_code=plant, wh_packing_func=True).first()
                    SAP_Inventory.objects.filter(month=month, warehouse=warehouse).delete()

                    for row in ws.iter_rows(min_row=2):
                        product_order = row[0].value
                        customer_no = row[1].value
                        mtr_desc = row[2].value
                        version_no = row[3].value
                        version_seq = row[4].value
                        size = row[5].value
                        qty = row[6].value
                        unit = row[7].value
                        location = row[8].value
                        post_date = row[9].value
                        location_desc = row[10].value
                        lot_no = row[11].value

                        item_type = ''
                        if row[2].value in ('內盒', 'ND-Hộp'):
                            item_type = 'PACKING_INNERBOX'
                        elif row[2].value in ('外箱', 'ND-Thùng'):
                            item_type = 'PACKING_OUTERBOX'

                        SAP_Inventory.objects.create(
                            month=month,
                            warehouse=warehouse,
                            product_order=product_order,
                            customer_no=customer_no,

                            mtr_desc=mtr_desc,
                            version_no=version_no,
                            version_seq=version_seq,
                            size=size,
                            qty=qty,
                            unit=unit,
                            location=location,
                            post_date=post_date,
                            location_desc=location_desc,
                            lot_no=lot_no,
                            item_type=item_type,
                            create_at=timezone.now(),
                            create_by=request.user
                        )
                    messages.success(request, _("import_successful"))

                    return redirect('sap_import')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = SAPUploadForm()

    return render(request, 'wh_packing/admin/sap_import.html', locals())


def sap_query_api(request):
    plant = request.GET.get('plant')
    month = request.GET.get('month')

    if plant and month:
        warehouse = Warehouse.objects.filter(wh_plant=plant, wh_packing_func=True).first()

        db = database()

        sql = f"""
        WITH MAIN AS (
                select 
                main.product_order,
                main.size,
                '{month}' month,
                main.version_no,
                main.customer_no,
                main.item_type
                from [wh_packing_sap_inventory] main 
                WHERE warehouse_id = '{warehouse}' AND month = '{month}' and item_type != '' and warehouse_id = '{warehouse}'
                union
                select 
                inv.product_order,
                inv.size,
                '{month}' month,
                inv.version_no,
                stin.customer_no,
                inv.item_type_id
                from [dbo].[wh_packing_bin_value] inv
                join [dbo].[wh_packing_stockinform] stin on inv.stockin_form = stin.form_no and inv.product_order = stin.product_order
                where inv.size in ('XXS','XS','S','M','L','XL','XXL') and inv.warehouse_id = '{warehouse}'
            ),
            INV_OUTERBOX AS (
                    select product_order,version_no,size,item_type_id,sum(qty) qty 
                    from [wh_packing_bin_value]
                    where item_type_id = 'PACKING_OUTERBOX' and warehouse_id = '{warehouse}'
                    group by product_order,version_no,size,item_type_id
            ),
            INV_INNERBOX AS (
                select product_order,version_no,size,item_type_id,sum(qty) qty 
                from [wh_packing_bin_value]
                where item_type_id = 'PACKING_INNERBOX' and warehouse_id = '{warehouse}'
                group by product_order,version_no,size,item_type_id
            ),
            SAP_OUTERBOX AS (
                select product_order,version_no,size,item_type,sum(qty) qty, post_date, month 
                from [dbo].[wh_packing_sap_inventory]
                where item_type = 'PACKING_OUTERBOX' and month='{month}' and warehouse_id = '{warehouse}'
                group by product_order,version_no,size,item_type, post_date, month
            ), 
            SAP_INNERBOX AS (
                select product_order,version_no,size,item_type,sum(qty) qty, post_date, month 
                from [dbo].[wh_packing_sap_inventory]
                where item_type = 'PACKING_INNERBOX' and month='{month}' and warehouse_id = '{warehouse}'
                group by product_order,version_no,size,item_type, post_date, month 
            ),
            PO_OUTERBOX AS (
                select product_order,version_no,size,item_type_id, purchase_qty
                from [wh_packing_stockinform]
                where item_type_id = 'PACKING_OUTERBOX'
                group by product_order,version_no,size,item_type_id, purchase_qty
            ),
            PO_INNERBOX AS (
                select product_order,version_no,size,item_type_id, purchase_qty
                from [wh_packing_stockinform]
                where item_type_id = 'PACKING_INNERBOX'
                group by product_order,version_no,size,item_type_id, purchase_qty
            ),
            LO_OUTERBOX AS (
                select product_order,version_no,size,lot_no, item_type, post_date, month
                from [dbo].[wh_packing_sap_inventory]
                where item_type = 'PACKING_OUTERBOX' and month='{month}' and warehouse_id = '{warehouse}'
                group by product_order,version_no,size,item_type, lot_no, post_date, month
            ), 
            LO_INNERBOX AS (
                select product_order,version_no,size,lot_no, item_type, post_date, month 
                from [dbo].[wh_packing_sap_inventory]
                where item_type = 'PACKING_INNERBOX' and month='{month}' and warehouse_id = '{warehouse}'
                group by product_order,version_no,size,item_type, lot_no, post_date, month
            ),
            LOT AS (
                select product_order,version_no,size,lot_no, post_date 
                from [dbo].[wh_packing_stockinform]
                group by product_order,version_no,size, lot_no, post_date
            )
            select 
                main.product_order,
                main.size,
                main.month,
                main.version_no,
                main.customer_no,
                MAX(outerbox_lo.lot_no) AS outer_lot,
                MAX(innerbox_lo.lot_no) AS inner_lot,
                MAX(outerbox_po.purchase_qty) AS outer_po,
                MAX(innerbox_po.purchase_qty) AS inner_po,
                MAX(outerbox_inv.qty) AS outer_inv,
                MAX(innerbox_inv.qty) AS inner_inv,
                MAX(outerbox_sap.qty) AS outer_sap,
                MAX(innerbox_sap.qty) AS inner_sap,
                MAX(outerbox_sap.post_date) AS outer_date,
                MAX(innerbox_sap.post_date) AS inner_date,
                MAX(lot_no.lot_no) AS lot_no
                from MAIN
            
                --PO
                LEFT JOIN PO_OUTERBOX AS outerbox_po
                    ON outerbox_po.product_order = main.product_order
                    AND outerbox_po.version_no = main.version_no
                    AND outerbox_po.size = main.size
                    AND outerbox_po.item_type_id = main.item_type
                    
                LEFT JOIN PO_INNERBOX AS innerbox_po
                    ON innerbox_po.product_order = main.product_order
                    AND innerbox_po.version_no = main.version_no
                    AND innerbox_po.size = main.size
                    AND innerbox_po.item_type_id = main.item_type
    
                --INV
                LEFT JOIN INV_OUTERBOX AS outerbox_inv
                    ON outerbox_inv.product_order = main.product_order
                    AND outerbox_inv.size = main.size
                    AND outerbox_inv.version_no = main.version_no
                    AND outerbox_inv.item_type_id = main.item_type
                LEFT JOIN INV_INNERBOX AS innerbox_inv
                    ON innerbox_inv.product_order = main.product_order
                    AND innerbox_inv.size = main.size
                    AND innerbox_inv.version_no = main.version_no
                    AND innerbox_inv.item_type_id = main.item_type
            
                --SAP
                LEFT JOIN SAP_OUTERBOX AS outerbox_sap
                    ON outerbox_sap.product_order = main.product_order
                    AND outerbox_sap.size = main.size
                    AND outerbox_sap.version_no = main.version_no
                    AND outerbox_sap.item_type = main.item_type
            
                LEFT JOIN SAP_INNERBOX AS innerbox_sap
                    ON innerbox_sap.product_order = main.product_order
                    AND innerbox_sap.size = main.size
                    AND innerbox_sap.version_no = main.version_no
                    AND innerbox_sap.item_type = main.item_type
    
                --LO
                LEFT JOIN LO_OUTERBOX AS outerbox_lo
                    ON outerbox_lo.product_order = main.product_order
                    AND outerbox_lo.size = main.size
                    AND outerbox_lo.version_no = main.version_no
                    AND outerbox_lo.item_type = main.item_type
    
                LEFT JOIN LO_INNERBOX AS innerbox_lo
                    ON innerbox_lo.product_order = main.product_order
                    AND innerbox_lo.size = main.size
                    AND innerbox_lo.version_no = main.version_no
                    AND innerbox_lo.item_type = main.item_type

                --LOT
                LEFT JOIN LOT AS lot_no
                    ON lot_no.product_order = main.product_order
                    AND lot_no.size = main.size
                    AND lot_no.version_no = main.version_no
            
            where main.month='{month}'
            GROUP BY main.product_order,
                        main.size,
                        main.month,
                        main.version_no,
                        main.customer_no
            
            ORDER BY product_order, version_no, customer_no, size ASC
            """
        data = db.select_sql_dict(sql)
        for item in data:
            outer_sap = item.get("outer_sap") or 0
            outer_inv = item.get("outer_inv") or 0
            inner_sap = item.get("inner_sap") or 0
            inner_inv = item.get("inner_inv") or 0

            item["outer_diff"] = outer_sap - outer_inv
            item["inner_diff"] = inner_sap - inner_inv
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse(
            {"status": "invalid", "message": "Invalid request data"},
            status=400
        )


@login_required
def sap_query(request):
    form = SAPQueryForm()
    return render(request, 'wh_packing/admin/sap_query.html', locals())


@login_required
def inventory_sheet(request):
    form = BinValueSearchForm(request.GET)
    results = []
    warehouses = Warehouse.objects.filter(wh_packing_func=True).values('wh_code', 'wh_plant')
    return render(request, 'wh_packing/search/bin_value_search.html',
                  {
                      'form': form,
                      'results': results,
                      'warehouses': warehouses,
                  })


@login_required
def inventory_deletion(request):
    form = BinValueDeleteForm(request.GET)
    results = []
    warehouses = Warehouse.objects.filter(wh_plant=request.user.plant)

    if form.is_valid():
        bin_id = form.cleaned_data.get('bin')
        if bin_id:
            results = Bin_Value.objects.filter(bin__bin_id=bin_id)

    return render(request, 'wh_packing/action/packing_bin_value_delete.html',
                  {'form': form, 'results': results, 'warehouses': warehouses})


def get_info_by_batch(request, batch=None):
    if batch:

        warehouse = Warehouse.objects.filter(wh_plant=request.user.plant,wh_packing_func=True).first()

        values = Bin_Value_History.objects.filter(warehouse=warehouse, batch_no=batch).values()

        return values
    else:
        return JsonResponse(
            {"error": "Batch Null"}, status=400
        )


@csrf_exempt
def get_hist_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        YYYYMM = datetime.now().strftime("%Y%m")
        key = "RVSE" + YYYYMM
        form_no = key + str(get_series_number(key, "RESERSE")).zfill(3)

        mvt = MovementType.objects.get(mvt_code="RVSE")

        with transaction.atomic():
            for item in data:
                warehouse_id = Warehouse.objects.get(wh_code=item['warehouse_id'])

                item_type = ItemType.objects.get(
                    Q(type_code=item['item_type_id']) |
                    Q(type_name=item['item_type_id']) |
                    Q(type_vn_name=item['item_type_id'])
                )
                item['item_type_id'] = item_type.type_code

                if item['plus_qty'] > 0:
                    qty = -item['plus_qty']
                elif item['minus_qty'] > 0:
                    qty = item['minus_qty']

                Do_Transaction(request,
                               form_no=form_no, warehouse=warehouse_id, product_order=item['product_order'],
                               purchase_no=item['purchase_no'], version_no=item['version_no'],
                               version_seq=item['version_seq'], item_code=item['item_type_id'], size=item['size'], mvt=mvt,
                               bin_code=item['bin_id'], qty=qty,
                               purchase_unit=item['purchase_unit'], desc='', stockin_form=item['batch_no'])

        return JsonResponse({'status': 'success'}, status=200)
    else:
        batch = request.GET.get('batch')
        transaction_rows = get_info_by_batch(request, batch=batch)
        return JsonResponse(list(transaction_rows), safe=False)


@login_required
def recover_stock(request):
    form = BatchSearchForm()
    return render(request, 'wh_packing/action/packing_recover_stock.html', locals())


@csrf_exempt
def inventory_delete(request):
    if request.method == "POST":

        data = json.loads(request.body)  # Đọc dữ liệu từ AJAX
        ids_to_delete = data.get("ids", [])

        YYYYMM = datetime.now().strftime("%Y%m")

        key = "DELT" + YYYYMM

        form_no = key + str(get_series_number(key, "DELT")).zfill(3)

        mvt = MovementType.objects.get(mvt_code="DELT")

        for id, info in data["list_data"].items():
            item_type = get_item_type_object(info['itemType'])

            bin = Bin.objects.select_related('area__warehouse').get(bin_id=info['binId'])
            area = bin.area
            warehouse = area.warehouse

            qty = int(info['qty']) * -1

            Do_Transaction(request, form_no, warehouse, info['productOrder'], info['purchaseNo'],
                           info['versionNo'], info['versionSeq'], item_type.type_code, info['size'],
                           mvt, info['binId'], qty, info['purchaseUnit'], desc="")

        if not ids_to_delete:
            return JsonResponse({"success": False, "error": "Không có dữ liệu để xóa!"})

    return JsonResponse({"success": False, "error": "Phương thức không hợp lệ!"})


# GET DATA
def get_areas(request):
    warehouse_id = request.GET.get('warehouse')
    areas = Area.objects.filter(warehouse_id=warehouse_id).values('area_id', 'area_name')
    return JsonResponse(list(areas), safe=False)


def get_all_areas(request):
    user = request.user
    plant = user.plant_id
    areas = Area.objects.filter(
        warehouse__wh_packing_func=True,
        warehouse__wh_plant=plant
    ).values('area_id', 'area_name', 'pos_y', 'pos_x', 'area_l', 'area_w', 'layer')
    return JsonResponse(list(areas), safe=False)


def get_bins(request):
    area_id = request.GET.get('area')
    bins = Bin.objects.filter(area_id=area_id).values('bin_id', 'bin_name').order_by('create_at')
    return JsonResponse(list(bins), safe=False)


def check_bin_exists(request):
    area_id = request.GET.get('area')
    bins = Bin.objects.filter(area_id=area_id).values('bin_id', 'bin_name').order_by('create_at')

    bin_data = []

    data_list = list(Bin_Value.objects.values_list("bin__bin_id", flat=True))

    for bin in bins:

        status = "red" if bin['bin_id'] in data_list else "green"  # Nếu tồn tại giá trị thì đỏ, ngược lại xanh

        bin_data.append({
            "bin_id": bin["bin_id"],
            "bin_name": bin["bin_name"],
            "status": status
        })

    return JsonResponse(bin_data, safe=False)


def get_bin_data(request):
    warehouse_id = request.GET.get("warehouse")
    area_id = request.GET.get("area")
    bin_id = request.GET.get("bin")
    po_id = request.GET.get("po")
    route_name = request.GET.get('route_name', '')

    if warehouse_id or area_id or bin_id or po_id:

        products = inventory_search(warehouse=warehouse_id, area=area_id, location=bin_id, product_order=po_id, route_name=route_name)

        return JsonResponse(list(products), safe=False)

    return JsonResponse([], safe=False)


# -- END DATA --

# UPDATE DATA
def update_user_plant(request):
    if request.method == "POST":
        plant_id = request.POST.get("plant")
        plant_obj = Plant.objects.get(plant_code=plant_id)

        with transaction.atomic():
            if plant_obj:
                CustomUser.objects.filter(id=request.user.id).update(plant=plant_obj)
    return redirect(request.META.get("HTTP_REFERER", "/"))

# -- END UPDATE DATA --


def download_excel_template(request, filename):
    file_path = os.path.join(settings.BASE_DIR, 'static/excel', filename)

    if not os.path.exists(file_path):
        raise Http404("File not exist")

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)


@login_required
def order_problem_page(request):
    form = BinValueSearchForm(request.GET)
    warehouses = Warehouse.objects.filter(wh_packing_func=True).values('wh_code', 'wh_plant')

    return render(request, 'wh_packing/search/order_problem.html', {'form': form, 'warehouses': warehouses})


def order_problem(request):
    warehouse_id = request.GET.get("warehouse")
    po_id = request.GET.get("po")
    lang = get_language()

    if warehouse_id:
        if lang == 'vi':
            when_condition = When(item_type__type_vn_name__isnull=False, then=F('item_type__type_vn_name'))
        elif lang == 'zh-hant':
            when_condition = When(item_type__type_name__isnull=False, then=F('item_type__type_name'))
        else:
            when_condition = When(item_type__type_code__isnull=False, then=F('item_type__type_code'))

        obj = Bin_Value.objects.filter(warehouse=warehouse_id)

        if po_id:
            obj = obj.filter(product_order=po_id)

        inv_system = list(obj.annotate(
            item_type_name=Case(
                when_condition,
                default=F('item_type__type_code'),
                output_field=CharField()
            )
        ))

        inv_search_list = inventory_id_search(warehouse=warehouse_id, product_order=po_id)
        inv_search = {list(d.values())[0] for d in inv_search_list}

        inv_search_sum = len(inv_search)
        inv_system_sum = len(inv_system)

        results = [item for item in inv_system if item.id not in inv_search]

        data = [
            {
                "id": item.id,
                "product_order": item.product_order,
                "purchase_no": item.purchase_no,
                "version_no": item.version_no,
                "version_seq": item.version_seq,
                "size": item.size,
                "qty": item.qty,
                "purchase_unit": item.purchase_unit,
                "stockin_form": item.stockin_form,
                "stockout_form": item.stockout_form,
                "update_at": item.update_at,
                "bin_id": item.bin_id,
                "item_type": item.item_type_name,
                "update_by": item.update_by.username,
            }
            for item in results
        ]

        return JsonResponse({"data": data, "system_sum": inv_system_sum, "search_sum": inv_search_sum}, safe=False)

    return JsonResponse([], safe=False)
