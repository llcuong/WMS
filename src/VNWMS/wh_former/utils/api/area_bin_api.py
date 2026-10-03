from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from warehouse.models import Area, Bin
import json
from VNWMS.database import database

@csrf_exempt
def bin_selection_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        area_id = data.get('area_id')
        total_basket_val = data.get('total_basket_val')

        former_size_master_data = data.get('size_name')
        former_size_stock_data = data.get('size')

        former_surface_master_data = data.get('surface_name')
        former_surface_stock_data = data.get('surface')

        wms_db = database()
        sql = f"""  SELECT 
                        wa.area_id,
                        wa.area_name,
                        wa.pos_x,
                        wa.pos_y,
                        wa.area_w,
                        wa.area_l,
                        ISNULL(b.total_baskets_bin, 0) AS basket_rows_from_bin,
                        ISNULL(b.total_qty_bin, 0) AS basket_qty_from_bin,
                        b.former_size,  -- thêm former_size
                        b.former_surface,
                        ISNULL(r.total_baskets_rack, 0) AS basket_rows_from_rack,
                        ISNULL(r.total_qty_rack, 0) AS basket_qty_from_rack,
                        -- tổng chung
                        ISNULL(b.total_baskets_bin, 0) + ISNULL(r.total_baskets_rack, 0) AS total_baskets,
                        ISNULL(b.total_qty_bin, 0) + ISNULL(r.total_qty_rack, 0) AS total_qty
                    FROM [GDWMS].[dbo].[warehouse_area] wa
                    LEFT JOIN (
                        SELECT 
                            fbind.bin, 
                            fbatch.former_size,
                            fbatch.former_surface,
                            COUNT(*) AS total_baskets_bin, 
                            SUM(fbind.basket_former_qty) AS total_qty_bin
                        FROM [GDWMS].[dbo].[wh_former_former_bin_data] fbind
                        INNER JOIN [GDWMS].[dbo].[wh_former_former_batch_data] fbatch
                            ON fbatch.batch_no = fbind.batch_no
                        GROUP BY fbind.bin, fbatch.former_size, fbatch.former_surface
                    ) b ON wa.area_name = b.bin
                    LEFT JOIN (
                        SELECT 
                            wffrbt.to_bin, 
                            COUNT(*) AS total_baskets_rack, 
                            SUM(wffrackbt.basket_former_qty) AS total_qty_rack
                        FROM [GDWMS].[dbo].[wh_former_former_rack_bin_temp] wffrbt
                        INNER JOIN [GDWMS].[dbo].[wh_former_former_rack_basket_temp] wffrackbt
                            ON wffrackbt.rack_temp_id = wffrbt.rack_temp_id
                        GROUP BY wffrbt.to_bin
                    ) r ON wa.area_name = r.to_bin
                    WHERE wa.area_name = '{area_id}';"""

        area_data = wms_db.select_sql_dict(sql)
        area_info = area_data[0]
        total_basket = int(area_info['total_baskets']) + int(total_basket_val)
        maximum_basket = int((int(area_info['area_w']) * int(area_info['area_l']) * 216) / (30 * 30))

        if (maximum_basket >= total_basket):
            if (former_size_master_data and former_surface_master_data) or (former_size_master_data is None and former_surface_master_data is None):
                if area_info['former_size'] is None and area_info['former_surface'] is None:
                    return JsonResponse({'status': 'ok', 'selected': area_id})

                if (former_size_master_data == area_info['former_size']) and (former_surface_master_data == area_info['former_surface']):
                    return JsonResponse({'status': 'ok', 'selected': area_id})

                else:
                    if 'Z' in area_id:
                        return JsonResponse({'status': 'ok', 'selected': area_id})
                    else:
                        return JsonResponse({'status': 'error', 'message': f'Can not add different types on same area !'})

            if former_size_stock_data and former_surface_stock_data:
                if area_info['former_size'] is None and area_info['former_surface'] is None:
                    return JsonResponse({'status': 'ok', 'selected': area_id})

                if (former_size_stock_data == area_info['former_size']) and (former_surface_stock_data == area_info['former_surface']):
                    return JsonResponse({'status': 'ok', 'selected': area_id})

                else:
                    if 'Z' in area_id:
                        return JsonResponse({'status': 'ok', 'selected': area_id})
                    else:
                        return JsonResponse({'status': 'error', 'message': f'Can not add different types on same area !'})

        else:
            if maximum_basket < total_basket:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Area {area_id} capacity exceeded! Maximum: {maximum_basket}, Required: {total_basket}'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Can not add different sizes on same area !'
                })


# @csrf_exempt
# def bin_selection_api(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         area_id = data.get('area_id')
#         bin_id = Bin.objects.filter(area__area_id=area_id).values_list('bin_id', flat=True)[0]
#         return JsonResponse({'status': 'ok', 'selected': bin_id})
@csrf_exempt
def get_area_batch_info(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Only POST method allowed'})

        body_data = json.loads(request.body)
        area_id = body_data.get('area_id')

        if not area_id:
            return JsonResponse({'success': False, 'message': 'area_id is required'})

        sql = f'''DECLARE @bin NVARCHAR(50) = N'{area_id}';
                WITH FB AS (
                    SELECT DISTINCT
                        fbind.batch_no,
                        fbind.bin,
                        fbatchd.former_size,
                        fbatchd.former_used_day,
                        fbatchd.former_length,
                        fbatchd.former_surface,
                        fbatchd.former_type,
                        fbatchd.former_vendor
                    FROM [GDWMS].[dbo].[wh_former_former_bin_data] AS fbind
                    JOIN [GDWMS].[dbo].[wh_former_former_batch_data] AS fbatchd
                      ON fbatchd.batch_no = fbind.batch_no
                    WHERE fbind.bin = @bin
                ),
                B AS (
                    SELECT
                        bin,
                        batch_no,
                        COUNT(*) AS total_baskets_bin,           
                        SUM(basket_former_qty) AS total_qty_bin
                    FROM [GDWMS].[dbo].[wh_former_former_bin_data]
                    WHERE bin = @bin
                    GROUP BY bin, batch_no
                ),
                R AS (
                    SELECT
                        wffrbt.to_bin AS bin,
                        wffrackbt.batch_no,
                        COUNT(*) AS total_baskets_rack,           
                        SUM(wffrackbt.basket_former_qty) AS total_qty_rack
                    FROM [GDWMS].[dbo].[wh_former_former_rack_bin_temp] AS wffrbt
                    JOIN [GDWMS].[dbo].[wh_former_former_rack_basket_temp] AS wffrackbt
                      ON wffrackbt.rack_temp_id = wffrbt.rack_temp_id
                    WHERE wffrbt.to_bin = @bin
                    GROUP BY wffrbt.to_bin, wffrackbt.batch_no
                )
                SELECT
                    FB.batch_no,
                    FB.former_size,
                    FB.former_used_day,
                    FB.former_length,
                    FB.former_surface,
                    FB.former_type,
                    FB.former_vendor,
                
                    ISNULL(B.total_baskets_bin, 0)  AS basket_rows_from_bin,
                    ISNULL(B.total_qty_bin, 0)      AS basket_qty_from_bin,
                    ISNULL(R.total_baskets_rack, 0) AS basket_rows_from_rack,
                    ISNULL(R.total_qty_rack, 0)     AS basket_qty_from_rack,
                    ISNULL(B.total_baskets_bin, 0) + ISNULL(R.total_baskets_rack, 0) AS total_baskets,
                    ISNULL(B.total_qty_bin, 0)     + ISNULL(R.total_qty_rack, 0)     AS total_qty
                FROM FB
                LEFT JOIN B ON B.bin = FB.bin AND B.batch_no = FB.batch_no
                LEFT JOIN R ON R.bin = FB.bin AND R.batch_no = FB.batch_no
                ORDER BY FB.batch_no;
            '''

        wms_db = database()
        data = wms_db.select_sql_dict(sql)
        if data:
            return JsonResponse({
                'success': True,
                'area_info': {
                    'area_id': area_id,
                    'batches': data,
                    'status': 'occupied' if data else 'available'
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'area_info': {
                    'area_id': area_id,
                    'batches': [],
                    'status': 'available'
                }
            })

    except Exception as e:
        print(f"Error in get_area_batch_info: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})



