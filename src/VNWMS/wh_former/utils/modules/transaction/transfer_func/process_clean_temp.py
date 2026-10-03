from wh_former.models import Basket_master_data, Former_rack_bin_temp, Former_batch_data, Former_rack_basket_temp, \
    Former_bin_data, Former_bin_data_log, RFID_read_log, Former_batch_data_log, Former_stockout_form

def _clean_temp(rack_bin_temps, rfid_reader_ip, batch_no, action):
    Former_rack_basket_temp.objects.filter(
        rack_temp_id__in=[rbt.rack_temp_id for rbt in rack_bin_temps],
        batch_no=batch_no
    ).delete()

    Former_rack_bin_temp.objects.filter(
        rack_temp_id__in=[rbt.rack_temp_id for rbt in rack_bin_temps],
        batch_no=batch_no
    ).delete()