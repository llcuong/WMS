from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _, get_language

from wh_former.models import Former_batch_data, Former_rack_bin_temp, Parameter_data
from django.db import connection
from VNWMS.database import database

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from wh_former.utils.utils import Bin_Selection
from wh_former.utils.modules.helpers.forms.former_form import convert_display_to_original
from datetime import datetime
import random
import string



def get_batch_no_api(request):
    itemno = request.GET.get('itemno')
    if not itemno:
        return JsonResponse({'error': _('Missing itemno')}, status=400)

    try:
        param = Parameter_data.objects.get(group='itemno', name=itemno)
    except Parameter_data.DoesNotExist:
        return JsonResponse({'error': _('Itemno not found')}, status=404)

    try:
        value = int(float(param.value))
    except (ValueError, TypeError):
        return JsonResponse({'error': _('Invalid value for itemno')}, status=400)

    batch_no = f"{itemno}{value:04d}"

    param.value = value + 1
    param.save(update_fields=['value'])

    print("Generated batch_no:", batch_no)
    return JsonResponse({'batch_no': batch_no})


def former_batch_detail_api(request):
    batch_no = request.GET.get('batch_no')
    if not batch_no:
        return JsonResponse({'error': 'Missing batch_no'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                batch.batch_no, 
                batch.former_vendor, 
                batch.former_receive_form, 
                batch.former_item_no, 
                batch.former_used_day, 
                batch.former_length, 
                bin.bin AS bin,
                COUNT(bin.basket_no) AS total_baskets,
                SUM(bin.basket_former_qty) AS total_formers
            FROM [GDWMS].[dbo].[wh_former_former_batch_data] batch
            LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] bin 
                ON batch.batch_no = bin.batch_no 
               AND bin.bin NOT LIKE '%%NBR%%'
            WHERE batch.batch_no = %s
              AND (bin.bin IS NOT NULL OR bin.bin > 0)
            GROUP BY 
                batch.batch_no, 
                batch.former_vendor, 
                batch.former_receive_form, 
                batch.former_item_no, 
                batch.former_used_day, 
                batch.former_length, 
                bin.bin
            HAVING COUNT(bin.basket_no) > 0 OR SUM(bin.basket_former_qty) > 0
            
            UNION ALL
            
            SELECT 
                batch.batch_no, 
                batch.former_vendor, 
                batch.former_receive_form, 
                batch.former_item_no, 
                batch.former_used_day, 
                batch.former_length, 
                stockout.stockout_to + '-' + RIGHT(stockout.stockout_form, 2) AS bin,
                stockout.stockout_total_basket - stockout.stockout_return_basket AS total_baskets,
                stockout.stockout_total_former - stockout.stockout_return_former AS total_formers
            FROM [GDWMS].[dbo].[wh_former_former_batch_data] batch
            LEFT JOIN [GDWMS].[dbo].[wh_former_former_stockout_form] stockout 
                ON batch.batch_no = stockout.batch_no 
               AND stockout.is_confirmed = 0
            WHERE batch.batch_no = %s
              AND stockout.stockout_to IS NOT NULL
              AND (
                    stockout.stockout_total_basket - stockout.stockout_return_basket > 0 
                 OR stockout.stockout_total_former - stockout.stockout_return_former > 0
                  )
            ORDER BY bin;
        """, [batch_no, batch_no])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]


    return JsonResponse({'detail': result})


def get_rack_bin_temp(request):
    rfid_reader_ip = request.GET.get('rfid_reader_ip', '').strip()
    action = request.GET.get('action', '').strip()
    batch_no = request.GET.get('batch_no', '').strip()

    if not rfid_reader_ip or not action:
        return JsonResponse({'error': _('rfid_reader_ip and action are required parameters')}, status=400)

    try:
        filter_kwargs = {
            'rfid_reader_ip': rfid_reader_ip,
            'action': action
        }
        
        if batch_no:
            filter_kwargs['batch_no'] = batch_no

        rack_bin_temp_data = Former_rack_bin_temp.objects.filter(
            **filter_kwargs
        ).exclude(rack_temp_id__isnull=True).values(
            'rack_temp_id', 'rack_scan_order', 'client_device_ip', 'action', 'from_bin', 'to_bin',
            'batch_no', 'rack_total_basket', 'rack_total_former'
        ).order_by('-rack_scan_order')

        html_content = render_to_string('wh_former/modules/components/tables/rack/rack_temp_table.html', {
            'rack_data': rack_bin_temp_data,
            'rfid_reader_ip': rfid_reader_ip,
            'action': action,
            'batch_no': batch_no or 'All batches',
            'filter_type': 'single_batch' if batch_no else 'reader_ip_action'
        })

        return JsonResponse({'html': html_content}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_rack_temp(request):
    rack_temp_id = request.POST.get('rack_temp_id')
    if not rack_temp_id:
        return JsonResponse({'error': 'Missing rack_temp_id'}, status=400)
    try:
        from wh_former.models import Former_rack_bin_temp, Former_rack_basket_temp
        Former_rack_bin_temp.objects.filter(rack_temp_id=rack_temp_id).delete()
        Former_rack_basket_temp.objects.filter(rack_temp_id=rack_temp_id).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_rack_stats(request):
    rfid_reader_ip = request.GET.get('rfid_reader_ip', '').strip()
    action = request.GET.get('action', '').strip()
    stats = {
        'rack_scanned': 0,
        'total_basket': 0,
        'total_former': 0
    }
    if rfid_reader_ip and action:
        temps = Former_rack_bin_temp.objects.filter(rfid_reader_ip=rfid_reader_ip, action=action)
        stats['rack_scanned'] = temps.count() if temps.exists() else 0
        stats['total_basket'] = temps.aggregate(total_basket=Sum('rack_total_basket'))['total_basket'] or 0
        stats['total_former'] = temps.aggregate(total_former=Sum('rack_total_former'))['total_former'] or 0
    return JsonResponse(stats)

def get_area_data_api(request):
    area_data = Bin_Selection()
    return JsonResponse({'area_data': area_data})

@require_POST
@csrf_exempt
def former_batch_update_api(request):

    import json
    
    try:
        data = json.loads(request.body)
        batch_no = data.get('batch_no')
        
        if not batch_no:
            return JsonResponse({'success': False, 'message': _('Missing batch_no')}, status=400)
        
        try:
            batch = Former_batch_data.objects.get(batch_no=batch_no)
        except Former_batch_data.DoesNotExist:
            return JsonResponse({'success': False, 'message': _('Batch not found')}, status=404)
        
        if 'former_receive_form' in data:
            batch.former_receive_form = data['former_receive_form']
        if 'former_vendor' in data:
            batch.former_vendor = data['former_vendor']
        if 'former_item_no' in data:
            batch.former_item_no = data['former_item_no']
        if 'former_length' in data:
            batch.former_length = data['former_length']
        if 'former_used_day' in data:
            batch.former_used_day = data['former_used_day']
        if 'former_size' in data:
            batch.former_size = data['former_size']
        if 'former_type' in data:
            batch.former_type = convert_display_to_original(data['former_type'])
        if 'former_surface' in data:
            batch.former_surface = convert_display_to_original(data['former_surface'])
        if 'former_purchase_order' in data:
            batch.former_purchase_order = data['former_purchase_order']
        if 'former_aql' in data:
            batch.former_aql = data['former_aql']
        if 'batch_data_date' in data:
            batch.batch_data_date = data['batch_data_date']
        
        batch.update_by = request.user

        batch.save()
        
        return JsonResponse({'success': True, 'message': _('Batch updated successfully')})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': _('Invalid JSON data')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def former_batch_full_detail_api(request):
    batch_no = request.GET.get('batch_no')
    if not batch_no:
        return JsonResponse({'success': False, 'error': _('Missing batch_no')}, status=400)

    try:
        batch = Former_batch_data.objects.get(batch_no=batch_no)
        batch_data = {
            'batch_no': batch.batch_no,
            'group_batch': batch.group_batch,
            'former_receive_form': batch.former_receive_form,
            'former_size': batch.former_size,
            'former_vendor': batch.former_vendor,
            'former_type': _(batch.former_type),
            'former_purchase_order': batch.former_purchase_order,
            'former_surface': _(batch.former_surface),
            'former_length': batch.former_length,
            'former_used_day': batch.former_used_day,
            'former_item_no': batch.former_item_no,
            'former_aql': batch.former_aql,
            'is_active': batch.is_active,
            'batch_data_date': batch.batch_data_date.strftime('%Y-%m-%d') if batch.batch_data_date else '',
            'batch_last_stockout': batch.batch_last_stockout.strftime('%Y-%m-%d') if batch.batch_last_stockout else '',
            'batch_total_basket': batch.batch_total_basket,
            'batch_total_former': batch.batch_total_former,
        }
        return JsonResponse({'success': True, 'batch_data': batch_data})
    except Former_batch_data.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Batch not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def former_batch_update_bin_api(request):
    import json
    from wh_former.models import Former_bin_data

    try:
        data = json.loads(request.body)
        batch_no = data.get('batch_no')
        new_bin = data.get('new_bin')
        old_bin = data.get('old_bin')

        if not batch_no or not new_bin:
            return JsonResponse({'success': False, 'message': 'Missing required data'}, status=400)

        wms_db = database()
        sql = f"""
            SELECT wa.area_id, wa.area_name, wa.pos_x, wa.pos_y, 
                wa.area_w, wa.area_l, COUNT(wffbd.basket_no) AS total_baskets, wffbatchd.former_size, wffbatchd.former_surface
            FROM [GDWMS].[dbo].[warehouse_area] wa
            LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] wffbd
                ON wa.[area_name] = wffbd.[bin]
            LEFT JOIN [GDWMS].[dbo].[wh_former_former_batch_data] wffbatchd
                ON wffbd.[batch_no] = wffbatchd.[batch_no] 
            WHERE wa.[area_name] = '{new_bin}'
            GROUP BY wa.area_id, wa.area_name, wa.pos_x, 
                        wa.pos_y, wa.area_w, wa.area_l, wffbatchd.former_size, wffbatchd.former_surface"""

        area_data = wms_db.select_sql_dict(sql)

        if not area_data:
            return JsonResponse({'success': False, 'message': _(f'Area {new_bin} not found')}, status=404)


        area_info = area_data[0]
        area_w = area_info['area_w']
        area_l = area_info['area_l']
        current_total_baskets = area_info['total_baskets']
        current_former_size = area_info['former_size']
        current_former_surface = area_info['former_surface']

        max_capacity = int((area_w * area_l * 216) / (30 * 30))


        change_sql = f"""
                    select COUNT(*) AS total_baskets_change, wffbatchd.former_size, wffbatchd.former_surface
                    from [GDWMS].[dbo].[wh_former_former_bin_data] wffbind
                    JOIN [GDWMS].[dbo].[wh_former_former_batch_data] wffbatchd
                    ON wffbatchd.batch_no = wffbind.batch_no
                    where wffbind.batch_no = '{batch_no}' and bin = '{old_bin}'
                    group by wffbatchd.former_size, wffbatchd.former_surface"""

        change_area_data = wms_db.select_sql_dict(change_sql)

        if not change_area_data:
            return JsonResponse({'success': False, 'message': f'Area {old_bin} not found'}, status=404)

        change_area_info = change_area_data[0]
        change_total_baskets = change_area_info['total_baskets_change']
        change_former_size = change_area_info['former_size']
        change_former_surface = change_area_info['former_surface']

        if (max_capacity >= (int(current_total_baskets) + int(change_total_baskets))):
            if ((change_former_size == current_former_size) and (change_former_surface == current_former_surface)) or (current_former_size is None):
                updated_count = Former_bin_data.objects.filter(
                    batch_no=batch_no, bin=old_bin
                ).update(bin=new_bin)

                if updated_count == 0:
                    return JsonResponse({'success': False, 'message': 'No records found to update'}, status=404)

                return JsonResponse({
                    'success': True, 'message': _(f'Updated records from {old_bin} to {new_bin}'), 'updated_count': updated_count})
            else:
                return JsonResponse({'success': False, 'message': _('Can not add different sizes on same area !')}, status=404)
        else:
            if max_capacity < (int(current_total_baskets) + int(change_total_baskets)):
                return JsonResponse({'success': False, 'message': _('Uplimit error. Can not move to new location')}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

from django.db import connection, transaction

@csrf_exempt
@require_POST
def batch_data_confirm_scrap(request):
    batch_no = request.POST.get("batch_no")
    basket_qty = request.POST.get("batch_basket_qty_stock")
    former_qty = request.POST.get("batch_qty_stock")
    key = request.POST.get("batch_key")

    if not batch_no or not key or len(key) < 16:
        return JsonResponse({"ok": False, "error": "Thiếu tham số hoặc key không hợp lệ"}, status=400)

    stockout_form = key[3:15]
    former_size = key[15:]

    try:
        with transaction.atomic():
            former_batch = (Former_batch_data.objects.select_for_update().filter(batch_no=batch_no).first())
            batch_current_total_former = None
            if former_batch:
                former_batch.batch_total_former = max(0, (former_batch.batch_total_former or 0) - int(former_qty))
                former_batch.batch_total_basket = max(0, (former_batch.batch_total_basket or 0) - int(basket_qty))
                former_batch.save(update_fields=["batch_total_former", "batch_total_basket"])
                batch_current_total_former = former_batch.batch_total_former

                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE [GDWMS].[dbo].[wh_former_former_stockout_form]
                        SET is_confirmed = 1
                        WHERE stockout_form = %s
                          AND former_size = %s
                          AND is_confirmed = 0
                    """, [stockout_form, former_size])

                    cursor.execute("""
                        UPDATE [GDWMS].[dbo].[wh_former_former_batch_data_log]
                        SET is_confirmed = 1
                        WHERE batch_sub_action_key = %s
                    """, [key])

        return JsonResponse({
            "ok": True,
            "batch_no": batch_no,
            "batch_current_total_former": batch_current_total_former,
        })

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def uhf_basket_data_api(request):
    tag_id = request.GET.get("tagId")
    if not tag_id:
        return JsonResponse({"error": "Missing tagId"}, status=400)

    # Escape input properly
    sql = f"""
        SELECT TOP (1)
            [basket_no],
            [basket_vendor],
            [basket_capacity],
            [basket_length],
            [basket_receive_date],
            [basket_purchase_order],
            [former_size],
            [former_used_day]
        FROM [GDWMS].[dbo].[wh_former_basket_master_data]
        WHERE basket_no = '{tag_id}'
    """

    wms_db = database()
    data = wms_db.select_sql_dict(sql)

    return JsonResponse({"data": data}, safe=False)


def uhf_stock_out_basket_data_api(request):
    tag_id = request.GET.get("tagId")
    if not tag_id:
        return JsonResponse({"error": "Missing tagId"}, status=400)

    sql = f"""
        SELECT TOP (1)
            bm.[basket_no],
            bm.[basket_vendor],
            bm.[basket_capacity],
            bm.[basket_length],
            bm.[basket_receive_date],
            bm.[basket_purchase_order],
            bm.[former_size],
            bm.[former_used_day],
            fb.[bin],
            fb.[basket_former_qty],
            fb.[batch_no],
            fb.[to_bin_key],
            fb.[update_at]
        FROM [GDWMS].[dbo].[wh_former_basket_master_data] bm
        INNER JOIN [GDWMS].[dbo].[wh_former_former_bin_data] fb
            ON bm.basket_no = fb.basket_no
        WHERE bm.basket_no = '{tag_id}'
    """

    wms_db = database()
    data = wms_db.select_sql_dict(sql)

    return JsonResponse({"data": data}, safe=False)


