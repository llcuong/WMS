from django.http import JsonResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from wh_former.forms import BasketMasterDataForm
from wh_former.utils.modules.helpers.forms.basket_form import extract_basket_form_data
from wh_former.utils.modules.helpers.forms.basket_form import clear_baskets_by_save_times

from wh_former.models import Former_master_data_scan_log
from datetime import datetime
from wh_former.utils.modules.helpers.forms.basket_form import get_basket_series
from barcode import Code128
from barcode.writer import SVGWriter
from urllib.parse import quote
import io


def basket_master_data_preview(request):
    if request.method == 'POST':
        form = BasketMasterDataForm(request.POST)
        success, msg, (basket_length, basket_vendor, fact_code,
                       basket_description, basket_receive_qty, basket_receive_date, basket_capacity,
                       basket_purchase_order, save_times) = extract_basket_form_data(request, form)
        prefix, start_series = get_basket_series(fact_code, basket_receive_date)
        basket_series = start_series
        basket_no = f"{prefix}{basket_series:06d}"

        if success:
            preview_data = {
                'basket_vendor': basket_vendor or '-',
                'basket_capacity': basket_capacity or '-',
                'basket_receive_qty': basket_receive_qty or '-',
                'basket_length': basket_length or '-',
                'basket_receive_date': basket_receive_date if basket_receive_date else '-',
                'basket_purchase_order': basket_purchase_order or '-',
                'basket_description': basket_description or '-',
                'fact_code': fact_code or 'N/A',
                'save_times': save_times,
                'preview_basket_no': f'{fact_code}{datetime.strptime(basket_receive_date, "%Y-%m-%d").strftime("%y%m%d")}______',
            }

            try:
                writer_opts = {
                    'write_text': False,
                    'module_width': 0.7,  # Make bars wider
                    'module_height': 12.0,  # Make barcode taller
                    'quiet_zone': 0,  # Add more space around barcode
                    'text_distance': 0,
                }
                code = Code128(basket_no, writer=SVGWriter())
                buf = io.BytesIO()
                code.write(buf, options=writer_opts)
                svg_text = buf.getvalue().decode('utf-8')
                svg_data_uri = f"data:image/svg+xml;utf8,{quote(svg_text)}"

                preview_data.update({
                    'basket_no': basket_no,
                    'barcode_svg_inline': svg_text,
                    'barcode_svg_data_uri': svg_data_uri,
                })

                return JsonResponse({'success': True, 'data': preview_data})


            except Exception as e:
                preview_data.update({
                    'basket_no': basket_no,
                    'barcode_error': str(e),
                })
                return JsonResponse({'success': True, 'data': preview_data, 'warning': 'Barcode render failed'})
        else:
            return JsonResponse({'success': False, 'data': msg})


@login_required
@csrf_exempt
def delete_basket_master_data(request):
    if request.method == 'POST':
        try:
            saved_timestamp = request.session.get('save_times')

            if not saved_timestamp:
                return JsonResponse({
                    'success': True,
                    'message': 'No recent baskets to clear',
                    'deleted_baskets': []
                })

            deleted_count, deleted_baskets = clear_baskets_by_save_times(saved_timestamp)

            request.session['save_times'] = None
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {deleted_count} basket records',
                'deleted_baskets': deleted_baskets,
                'deleted_count': deleted_count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting basket data: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
def check_purchase_order_data(request):
    """
    API endpoint to check if former receive form exists in database
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        # Parse JSON body
        body = json.loads(request.body)
        former_receive_form = body.get('former_receive_form', '').strip().upper()

        if not former_receive_form or len(former_receive_form) != 9:
            return JsonResponse({'success': False, 'error': 'Former receive form must be exactly 9 characters'})

        with connection.cursor() as cursor:
            # Tìm trong bảng former master data hoặc bảng liên quan
            cursor.execute("""
                SELECT TOP 1 
                    batch_dn,
                    batch_item_no,
                    batch_used_day,
                    batch_purchase_order,
                    batch_data_date,
                    batch_former_vendor,
                    batch_former_type,
                    batch_former_surface,
                    batch_former_size,
                    batch_former_length,
                    batch_former_aql,
                    batch_no,
                    batch_purchase_received
                FROM [GDWMS].[dbo].[wh_former_former_master_data_scan_log]
                WHERE batch_dn = %s
                ORDER BY id DESC
            """, [former_receive_form])

            result = cursor.fetchone()
            if result:
                data = {
                    'former_receive_form': result[0],
                    'batch_item_no': result[1],
                    'batch_used_day': result[2],
                    'batch_purchase_order': result[3],
                    'batch_data_date': result[4].strftime('%Y-%m-%d') if result[4] else '',
                    'batch_former_vendor': result[5],
                    'batch_former_type': result[6],
                    'batch_former_surface': result[7],
                    'batch_former_size': result[8],
                    'batch_former_length': result[9],
                    'batch_former_aql': result[10],
                    'batch_no': result[11]
                }
                return JsonResponse({'success': True, 'data': data})
            else:
                return JsonResponse({'success': False, 'error': 'Former receive form not found'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'})
    except Exception as e:
        print(f"Error checking former receive form: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def check_former_form_data(request):
    """
    POST:
      - former_purchase_order: string (required length >= 10)
    Return:
      { success: bool, found: bool, data?: {...} }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'METHOD_NOT_ALLOWED'}, status=405)

    po = (request.POST.get('former_purchase_order') or '').strip().upper()
    if len(po) < 10:
        return JsonResponse({'success': False, 'error': 'INVALID_PO'}, status=400)

    # Một PO có thể có nhiều log; lấy bản mới nhất theo id hoặc thời điểm (tuỳ model)
    qs = Former_master_data_scan_log.objects.filter(batch_purchase_order=po)

    if not qs.exists():
        return JsonResponse({'success': True, 'found': False})

    # Nếu có cột thời gian (vd: create_at) thì .latest('create_at'); nếu không, dùng id
    try:
        log = qs.latest('id')
    except Exception:
        log = qs.order_by('-id').first()

    data = {
        'batch_dn': log.batch_dn,
        'batch_item_no': log.batch_item_no,
        'batch_used_day': log.batch_used_day,
        'batch_purchase_order': log.batch_purchase_order,
        'batch_data_date': (log.batch_data_date.isoformat() if getattr(log, 'batch_data_date', None) else None),
        'batch_former_vendor': log.batch_former_vendor,
        'batch_former_type': log.batch_former_type,
        'batch_former_surface': log.batch_former_surface,
        'batch_former_size': log.batch_former_size,
        'batch_former_length': log.batch_former_length,
        'batch_former_aql': log.batch_former_aql,
        'batch_no': log.batch_no,
        'batch_purchase_received': log.batch_purchase_received,
    }
    return JsonResponse({'success': True, 'found': True, 'data': data}, json_dumps_params={'ensure_ascii': False})
