from wh_former.models import Former_rack_bin_temp, Former_rack_basket_temp

def Cancel_Operation(request, rfid_reader_ip, action):
    try:
        rack_bin_temps = Former_rack_bin_temp.objects.filter(
            rfid_reader_ip=rfid_reader_ip,
            action=action
        )

        if rack_bin_temps.exists():

            if not rack_bin_temps.exists():
                return False, f"No temp data found for action {action}", 0, 0

            rack_temp_ids = list(rack_bin_temps.values_list('rack_temp_id', flat=True))

            deleted_baskets = Former_rack_basket_temp.objects.filter(
                rack_temp_id__in=rack_temp_ids
            ).count()

            Former_rack_basket_temp.objects.filter(
                rack_temp_id__in=rack_temp_ids
            ).delete()

            deleted_racks = rack_bin_temps.count()
            rack_bin_temps.delete()

            rack_scanned = 0
            return True, rack_scanned, 0, 0
        else:
            return True, 0, 0, 0
    except action:
        return False, f"Movement type {action} does not exist", 0, 0
    except Exception as e:
        return False, f"Error cancelling operation: {str(e)}", 0, 0