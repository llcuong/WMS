from wh_former.utils.helpers.map_helpers import get_former_area_coords, get_former_area_bin, parse_bin_structure, \
    convert_defaultdict_to_dict


def Bin_Selection():
    area_data = get_former_area_coords()

    for area in area_data:

        area['bins'] = []

        area_bin = get_former_area_bin(area['id'])
        if area_bin:
            area['batch_no'] = sum(b['batch_no'] for b in area_bin)
        else:
            area['batch_no'] = 0

        bin_bin = parse_bin_structure(
            area_bin,
            area['id'],
            area['x'],
            area['y'],
            area['w'],
            area['l'],
        )
        for row in bin_bin:
            for col in bin_bin[row]:
                for b in bin_bin[row][col]:
                    b['x'] -= area['x']
                    b['y'] -= area['y']

        area['bins'] = convert_defaultdict_to_dict(bin_bin)

    return area_data

