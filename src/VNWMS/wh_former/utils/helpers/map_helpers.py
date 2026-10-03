from warehouse.models import Area, Bin
from wh_former.models import Former_bin_data
from django.db.models import OuterRef, Subquery, Q

import re
from collections import defaultdict



def get_former_area_coords():
    point_list = Area.objects.filter(warehouse__wh_former_func=True, area_id__icontains='FM').exclude(
        Q(warehouse__wh_code__icontains='MACH')
    )
    if point_list:
        area_data = [
            {
                'id': area.area_id,
                'name': area.area_name,
                'x': area.pos_x or 0,
                'y': area.pos_y or 0,
                'w': area.area_w or 0,
                'l': area.area_l or 0,
            }
            for area in point_list
        ]

    else:
        area_data = []

    return area_data





def get_former_area_bin(area_id):
    # sql = """
    #     SELECT
    #         b.bin_id,
    #         b.bin_name,
    #         COUNT(fbd.batch_no) + COUNT(frbt.batch_no) AS batch_count
    #     FROM [GDWMS].[dbo].[warehouse_bin] b
    #     LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] fbd
    #         ON fbd.bin = b.bin_id
    #     LEFT JOIN [GDWMS].[dbo].[wh_former_former_rack_bin_temp] frbt
    #         ON frbt.from_bin = b.bin_id
    #     LEFT JOIN [GDWMS].[dbo].[wh_former_former_rack_basket_temp] frbaskett
    #         ON frbaskett.rack_temp_id = frbt.rack_temp_id
    #     WHERE b.area_id = %s
    #     GROUP BY b.bin_id, b.bin_name
    #     ORDER BY b.bin_id
    # """

    sql = """
        SELECT
            b.bin_id,
            b.bin_name,
            count(u.basket_no) as batch_count
        FROM [GDWMS].[dbo].[warehouse_bin] b
        LEFT JOIN (
            SELECT fbd.bin AS bin_id, fbd.basket_no
            FROM [GDWMS].[dbo].[wh_former_former_bin_data] fbd
        
            UNION
            SELECT frbt.from_bin AS bin_id, frbaskett.basket_no
            FROM [GDWMS].[dbo].[wh_former_former_rack_bin_temp] frbt
            JOIN [GDWMS].[dbo].[wh_former_former_rack_basket_temp] frbaskett
              ON frbaskett.rack_temp_id = frbt.rack_temp_id
            ) AS u
            ON u.bin_id = b.bin_id
        WHERE b.area_id = %s
        GROUP BY b.bin_id, b.bin_name
        ORDER BY b.bin_id;
    """

    bin_list = Bin.objects.raw(sql, [area_id])

    bin_data = []
    for bin in bin_list:
        bin_data.append({
            'bin_id': bin.bin_id,
            'bin_name': bin.bin_name,
            'batch_no': bin.batch_count
        })
    return bin_data





def parse_bin_structure(bin_list, area_prefix, area_x, area_y, area_w, area_l):
    rows = defaultdict(lambda: defaultdict(list))

    clean_prefix = area_prefix.replace('FM-', '') if area_prefix.startswith('FM-') else area_prefix

    pattern = re.compile(rf'^{clean_prefix}-(\d+)-([A-Z])$')
    max_row = 0
    positions = set()  # Lưu các vị trí (row) duy nhất

    for bin_item in bin_list:
        bin_id = bin_item['bin_id']
        match = pattern.match(bin_id)

        if match:
            row = int(match.group(1))
            level_char = match.group(2)
            # A = tầng 2, B = tầng 1
            level = 2 if level_char == 'A' else 1
            max_row = max(max_row, row)
            positions.add(row)

            rows[row][level].append({
                'bin_id': bin_id,
                'level': level,
                'batch': bin_item['batch_no']
            })

    # Mỗi bin 30x30
    bin_w = 30
    bin_l = 30

    # Tính số cột dựa trên area width
    max_cols = area_w // bin_w if bin_w > 0 else 1

    for row, levels in rows.items():
        # Tính vị trí x, y cho row này
        col_index = (row - 1) % max_cols  # Chia thành cột
        row_index = (row - 1) // max_cols  # Chia thành hàng

        bin_x = area_x + col_index * bin_w
        bin_y = area_y + row_index * bin_l

        for level, bins in levels.items():
            for b in bins:
                # A và B cùng x, y nhưng khác level
                b['x'] = bin_x
                b['y'] = bin_y
                b['w'] = bin_w
                b['l'] = bin_l

    return rows



def convert_defaultdict_to_dict(obj):
    if isinstance(obj, defaultdict):
        return {k: convert_defaultdict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {k: convert_defaultdict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_defaultdict_to_dict(i) for i in obj]
    else:
        return obj