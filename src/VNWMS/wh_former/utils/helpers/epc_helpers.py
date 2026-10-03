from wh_former.models import Basket_master_data, Basket_master_data_log, Former_bin_data, Former_rack_basket_temp, \
    Former_rack_bin_temp, Former_stockout_form

from datetime import datetime
from django.db.models import Q



def get_basket_series(fact_code):
    prefix = f"{fact_code}{datetime.now().strftime('%y%m%d')}"

    latest_log = Basket_master_data_log.objects.filter(
        basket_no__basket_no__startswith=f"{prefix}"
    ).order_by('-basket_series').first()

    next_series = latest_log.basket_series + 1 if latest_log else 1
    return prefix, next_series


def get_basket_no(fact_code):
    prefix, series = get_basket_series(fact_code)
    return f"{prefix}" + f"{series:06d}"


def get_former_master_data(basket_no, pid, machine, origin_bin, selected_bin_code):

    if basket_no:
        temp_exists = Former_rack_basket_temp.objects.filter(basket_no=basket_no).exists()
        if temp_exists:
            return None

        if int(pid) == 1 or int(pid) == 2:
            already_in_bin = Former_bin_data.objects.filter(
                    basket_no=basket_no
                ).exclude(
                    Q(bin__istartswith='FM') # | Q(bin__istartswith='NBR')
                )
            if already_in_bin.exists():
                return None
            else:
                basket_vendor = Basket_master_data.objects.filter(basket_no=basket_no).values_list('basket_vendor', flat=True).first()
                if not basket_vendor:
                    basket_vendor = 'UNKNOWN'

                if int(pid) == 1:
                    return [basket_no, 5, basket_vendor, '']
                if int(pid) == 2:
                    return [basket_no, 1, basket_vendor, '']

        elif int(pid) == 3:
            already_in_bin = Former_bin_data.objects.filter(basket_no=basket_no).first()
            if not already_in_bin:
                return None
            else:
                if already_in_bin.bin != selected_bin_code:
                    return None
                basket_master = Basket_master_data.objects.filter(basket_no=basket_no).first()

                if not basket_master:
                    return None

                if basket_master.is_active == 0:
                    return None

                if not basket_master.basket_vendor:
                    basket_vendor = 'UNKNOWN'
                else:
                    basket_vendor = basket_master.basket_vendor

                bin_data = Former_bin_data.objects.filter(basket_no=basket_no).first()
                if bin_data:
                    # OLD LOGIC: Check if stockout from same bin only
                    # if origin_bin != 'NONE':
                    #     if 'NBR' in bin_data.bin or 'CLEAN' in bin_data.bin:
                    #         return None
                    #     elif origin_bin != bin_data.bin and 'Z' not in bin_data.bin:
                    #         return [basket_no, bin_data.basket_former_qty, basket_vendor, 'KHÁC BIN CŨ']
                    #     elif origin_bin == bin_data.bin or 'Z' in bin_data.bin:
                    #         return [basket_no, bin_data.basket_former_qty, basket_vendor, bin_data.bin]
                    # else:
                    #     if 'NBR' in bin_data.bin or 'CLEAN' in bin_data.bin:
                    #         return None
                    #     else:
                    #         return [basket_no, bin_data.basket_former_qty, basket_vendor, bin_data.bin]
                    
                    # NEW LOGIC: Allow stockout from any bin (no bin check)
                    if 'NBR' in bin_data.bin or 'CLEAN' in bin_data.bin:
                        return None
                    return [basket_no, bin_data.basket_former_qty, basket_vendor, bin_data.bin]

        elif int(pid) == 5 or int(pid) == 6 or int(pid) == 7:
            already_in_bin = Former_bin_data.objects.filter(basket_no=basket_no)
            if not already_in_bin.exists():
                return None
            else:
                basket_master = Basket_master_data.objects.filter(basket_no=basket_no).first()

                if not basket_master:
                    return None

                if basket_master.is_active == 0:
                    return None

                if not basket_master.basket_vendor:
                    basket_vendor = 'UNKNOWN'
                else:
                    basket_vendor = basket_master.basket_vendor
                bin_data = Former_bin_data.objects.filter(basket_no=basket_no).first()
                if bin_data:
                    if 'NBR' in bin_data.bin or 'CLEAN' in bin_data.bin:
                        if int(pid) == 5:
                            return [basket_no, 5, basket_vendor, bin_data.bin]
                        if int(pid) == 6:
                            return [basket_no, 1, basket_vendor, bin_data.bin]
                        if int(pid) == 7:
                            return [basket_no, 0, basket_vendor, bin_data.bin]

