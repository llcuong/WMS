from wh_former.models import Basket_master_data, Former_rack_bin_temp, Former_batch_data, Former_rack_basket_temp, \
    Former_bin_data, Former_bin_data_log, RFID_read_log, Former_batch_data_log, Former_stockout_form, Former_master_data_scan_log

from django.utils import timezone
from django.db.models import F

from wh_former.utils.modules.transaction.transfer_func.process_basket_transfers import _basket_transfers

from datetime import date, datetime

from wh_former.utils.modules.helpers.forms.former_form import handle_form_input_log


def _batch_update(batch_no, batch_no_obj, total_baskets_all, total_formers_all, final_used_day, action,
                                 user, operation_type, batch_no_list=None, max_former_batch=None, key=None,
                                    total_stock_basket=None, total_stock_former=None, form_batch_no=None, stockin_from=None, stockout_to=None):

    original_basket_qty = batch_no_obj.batch_total_basket or 0
    original_former_qty = batch_no_obj.batch_total_former or 0

    if operation_type == 'stockin':
        if action == 'CRTE':
            get_batch_exist = Former_batch_data_log.objects.filter(batch_no=batch_no)
            if not get_batch_exist.exists():
                Former_batch_data_log.objects.create(
                    batch_no=batch_no,
                    batch_action_name=action,

                    batch_qty_merge=total_formers_all,
                    batch_qty_in_wh=original_former_qty+total_formers_all,
                    batch_qty_total=original_former_qty+total_formers_all,
                    batch_qty_stockin=total_formers_all,

                    batch_used_day=final_used_day,

                    batch_basket_qty_merge=total_baskets_all,
                    batch_basket_qty_in_wh=original_basket_qty+total_baskets_all,
                    batch_basket_qty_total=original_basket_qty+total_baskets_all,
                    batch_basket_qty_stockin=total_baskets_all,
                )

                Former_batch_data.objects.filter(batch_no=batch_no).update(
                    batch_total_basket=original_basket_qty+total_baskets_all,
                    batch_total_basket_in_wh=original_basket_qty+total_baskets_all,
                    batch_total_former=original_former_qty+total_formers_all,
                    batch_total_former_in_wh=original_former_qty+total_formers_all,
                    former_used_day=final_used_day,
                    update_by=user,
                    update_at=timezone.now()
                )

                Former_master_data_scan_log.objects.filter(batch_no=batch_no).update(
                    batch_purchase_received=F('batch_purchase_received') + total_formers_all
                )

            else:
                lasted_batch_data_log = Former_batch_data_log.objects.filter(batch_no=batch_no).order_by('-id').first()
                final_used_day = 0 if total_formers_all / (total_formers_all + lasted_batch_data_log.batch_qty_total) > 0.8 else final_used_day

                if lasted_batch_data_log.batch_action_name == 'CRTE':
                    lasted_batch_data_log.batch_qty_merge += total_formers_all
                    lasted_batch_data_log.batch_qty_in_wh = lasted_batch_data_log.batch_qty_total + total_formers_all
                    lasted_batch_data_log.batch_qty_total += total_formers_all
                    lasted_batch_data_log.batch_qty_stockin += total_formers_all

                    lasted_batch_data_log.batch_basket_qty_merge += total_baskets_all
                    lasted_batch_data_log.batch_basket_qty_in_wh = lasted_batch_data_log.batch_basket_qty_total + total_baskets_all
                    lasted_batch_data_log.batch_basket_qty_total += total_baskets_all
                    lasted_batch_data_log.batch_basket_qty_stockin += total_baskets_all

                    lasted_batch_data_log.save()

                    lasted_batch_data = Former_batch_data.objects.filter(batch_no=batch_no).first()
                    if lasted_batch_data:
                        lasted_batch_data.batch_total_basket += total_baskets_all
                        lasted_batch_data.batch_total_former += total_formers_all
                        lasted_batch_data.batch_total_basket_in_wh += total_baskets_all
                        lasted_batch_data.batch_total_former_in_wh += total_formers_all
                        lasted_batch_data.former_used_day = final_used_day
                        lasted_batch_data.save()

                    Former_master_data_scan_log.objects.filter(batch_no=batch_no).update(
                        batch_purchase_received=F('batch_purchase_received') + total_formers_all
                    )

                else:
                    Former_batch_data_log.objects.create(
                        batch_no=batch_no,
                        batch_action_name=action,

                        batch_qty_merge=total_formers_all,
                        batch_qty_in_wh=lasted_batch_data_log.batch_qty_in_wh + total_formers_all,
                        batch_qty_total=lasted_batch_data_log.batch_qty_total + total_formers_all,
                        batch_qty_stockin=lasted_batch_data_log.batch_qty_stockin + total_formers_all,

                        batch_basket_qty_merge=total_baskets_all,
                        batch_basket_qty_in_wh=lasted_batch_data_log.batch_basket_qty_in_wh + total_baskets_all,
                        batch_basket_qty_total=lasted_batch_data_log.batch_basket_qty_total + total_baskets_all,
                        batch_basket_qty_stockin=lasted_batch_data_log.batch_basket_qty_stockin + total_baskets_all,

                        batch_used_day=final_used_day,
                    )

                    lasted_batch_data = Former_batch_data.objects.filter(batch_no=batch_no).first()
                    if lasted_batch_data:
                        lasted_batch_data.batch_total_basket += total_baskets_all
                        lasted_batch_data.batch_total_former += total_formers_all
                        lasted_batch_data.batch_total_basket_in_wh += total_baskets_all
                        lasted_batch_data.batch_total_former_in_wh += total_formers_all
                        lasted_batch_data.former_used_day = final_used_day
                        lasted_batch_data.save()

                    Former_master_data_scan_log.objects.filter(batch_no=batch_no).update(
                        batch_purchase_received=F('batch_purchase_received') + total_formers_all
                    )

        elif action == 'STIN':
            get_batch_exist = Former_batch_data.objects.filter(batch_no=batch_no).first()
            if get_batch_exist:
                get_batch_log_exist = Former_batch_data_log.objects.filter(batch_no=batch_no, batch_action_name=action, batch_sub_action_key=key)
                if not get_batch_log_exist:
                    Former_batch_data_log.objects.create(
                        batch_no=batch_no,
                        batch_action_name=action,
                        batch_sub_action_key=key,

                        batch_qty_in_wh=get_batch_exist.batch_total_former_in_wh + total_formers_all,
                        batch_qty_total=get_batch_exist.batch_total_former,
                        batch_qty_stockin=total_formers_all,

                        batch_basket_qty_in_wh=get_batch_exist.batch_total_basket_in_wh + total_baskets_all,
                        batch_basket_qty_total=get_batch_exist.batch_total_basket,
                        batch_basket_qty_stockin=total_baskets_all,

                        batch_used_day=final_used_day,
                    )

                    get_batch_exist.batch_total_basket_in_wh += total_baskets_all
                    get_batch_exist.batch_total_former_in_wh += total_formers_all
                    get_batch_exist.former_used_day = final_used_day
                    get_batch_exist.save()

                else:
                    lasted_batch_data_log = get_batch_log_exist.first()
                    lasted_batch_data_log.batch_qty_in_wh += total_formers_all
                    lasted_batch_data_log.batch_qty_stockin += total_formers_all
                    lasted_batch_data_log.batch_basket_qty_in_wh += total_baskets_all
                    lasted_batch_data_log.batch_basket_qty_stockin += total_baskets_all
                    lasted_batch_data_log.save()

                    get_batch_exist.batch_total_basket_in_wh += total_baskets_all
                    get_batch_exist.batch_total_former_in_wh += total_formers_all
                    # get_batch_exist.former_used_day = final_used_day
                    get_batch_exist.save()

    elif operation_type == 'stockout':
        get_batch_key = Former_batch_data_log.objects.filter(batch_sub_action_key=key, batch_action_name=action)
        if not get_batch_key.exists():
            if batch_no == form_batch_no:
                const_final_used_day = final_used_day

                final_used_day = (
                    Former_batch_data.objects
                        .filter(batch_no=batch_no)
                        .values_list('former_used_day', flat=True)
                        .first()
                )

                final_used_day = final_used_day if final_used_day is not None else const_final_used_day

                Former_batch_data_log.objects.create(
                    batch_no=batch_no,
                    batch_combine='',
                    batch_action_name=action,
                    batch_sub_action_name='MERGE',
                    batch_sub_action_key=key,

                    batch_qty_stockout=total_formers_all,
                    batch_qty_in_wh=original_former_qty-total_formers_all,
                    batch_qty_total=original_former_qty,

                    batch_basket_qty_stockout=total_baskets_all,
                    batch_basket_qty_in_wh=original_basket_qty-total_baskets_all,
                    batch_basket_qty_total=original_basket_qty,

                    batch_used_day=final_used_day,
                )

                Former_batch_data.objects.filter(batch_no=batch_no).update(
                    batch_total_basket=original_basket_qty,
                    batch_total_former=original_former_qty,

                    batch_total_basket_in_wh=original_basket_qty-total_baskets_all,
                    batch_total_former_in_wh=original_former_qty-total_formers_all,

                    former_used_day=final_used_day,
                    update_by=user,
                    update_at=timezone.now()
                )

        elif get_batch_key.exists():
            if batch_no != form_batch_no:
                get_batch_exist = Former_batch_data_log.objects.filter(batch_no=batch_no, batch_sub_action_key=key, batch_action_name=action)

                const_final_used_day = final_used_day

                final_used_day = (
                    Former_batch_data.objects
                        .filter(batch_no=batch_no)
                        .values_list('former_used_day', flat=True)
                        .first()
                )

                final_used_day = final_used_day if final_used_day is not None else const_final_used_day

                if not get_batch_exist.exists():
                    Former_batch_data_log.objects.create(
                        batch_no=batch_no,
                        batch_combine=form_batch_no,
                        batch_action_name=action,
                        batch_sub_action_name='SPLIT',
                        batch_sub_action_key=key,

                        batch_qty_stockout=total_formers_all,
                        batch_qty_split=-total_formers_all,
                        batch_qty_in_wh=original_former_qty-total_formers_all,
                        batch_qty_total=original_former_qty-total_formers_all,

                        batch_basket_qty_stockout=total_baskets_all,
                        batch_basket_qty_split=-total_baskets_all,
                        batch_basket_qty_in_wh=original_basket_qty-total_baskets_all,
                        batch_basket_qty_total=original_basket_qty - total_baskets_all,

                        batch_used_day=final_used_day,
                    )

                    Former_batch_data.objects.filter(batch_no=batch_no).update(
                        batch_total_basket=original_basket_qty-total_baskets_all,
                        batch_total_former=original_former_qty-total_formers_all,

                        batch_total_basket_in_wh=original_basket_qty-total_baskets_all,
                        batch_total_former_in_wh=original_former_qty-total_formers_all,

                        former_used_day=final_used_day,
                        update_by=user,
                        update_at=timezone.now()
                    )

                    merge_batch_log_obj = Former_batch_data_log.objects.filter(batch_no=form_batch_no, batch_sub_action_key=key, batch_action_name=action).first()
                    if merge_batch_log_obj:
                        merge_batch_log_obj.batch_qty_merge += total_formers_all
                        merge_batch_log_obj.batch_qty_total += total_formers_all
                        merge_batch_log_obj.batch_basket_qty_merge += total_baskets_all
                        merge_batch_log_obj.batch_basket_qty_total += total_baskets_all
                        merge_batch_log_obj.save()

                    merge_batch_obj = Former_batch_data.objects.filter(batch_no=form_batch_no).first()
                    if merge_batch_obj:
                        merge_batch_obj.batch_total_basket += total_baskets_all
                        merge_batch_obj.batch_total_former += total_formers_all
                        merge_batch_obj.save()

                else:
                    split_batch_log_obj = Former_batch_data_log.objects.filter(batch_no=batch_no, batch_sub_action_key=key, batch_action_name=action).first()
                    if split_batch_log_obj:
                        split_batch_log_obj.batch_qty_stockout += total_formers_all
                        split_batch_log_obj.batch_qty_split -= total_formers_all
                        split_batch_log_obj.batch_qty_in_wh -= total_formers_all
                        split_batch_log_obj.batch_qty_total -= total_formers_all
                        split_batch_log_obj.batch_basket_qty_stockout += total_baskets_all
                        split_batch_log_obj.batch_basket_qty_split -= total_baskets_all
                        split_batch_log_obj.batch_basket_qty_in_wh -= total_baskets_all
                        split_batch_log_obj.batch_basket_qty_total -= total_baskets_all
                        split_batch_log_obj.save()


                    split_batch_obj = Former_batch_data.objects.filter(batch_no=batch_no).first()
                    if split_batch_obj:
                        split_batch_obj.batch_total_basket -= total_baskets_all
                        split_batch_obj.batch_total_former -= total_formers_all

                        split_batch_obj.batch_total_basket_in_wh -= total_baskets_all
                        split_batch_obj.batch_total_former_in_wh -= total_formers_all

                        split_batch_obj.save()


                    merge_batch_log_obj = Former_batch_data_log.objects.filter(batch_no=form_batch_no, batch_sub_action_key=key, batch_action_name=action).first()
                    if merge_batch_log_obj:
                        merge_batch_log_obj.batch_qty_merge += total_formers_all
                        merge_batch_log_obj.batch_qty_total += total_formers_all
                        merge_batch_log_obj.batch_qty_basket_merge += total_baskets_all
                        merge_batch_log_obj.batch_qty_basket_total += total_baskets_all
                        merge_batch_log_obj.save()

                    merge_batch_obj = Former_batch_data.objects.filter(batch_no=form_batch_no).first()
                    if merge_batch_obj:
                        merge_batch_obj.batch_total_basket += total_baskets_all
                        merge_batch_obj.batch_total_former += total_formers_all
                        merge_batch_obj.save()


            elif batch_no == form_batch_no:
                get_batch_exist = Former_batch_data_log.objects.filter(batch_no=batch_no, batch_sub_action_key=key, batch_action_name=action)

                if get_batch_exist.exists():
                    merge_batch_log_obj = get_batch_exist.first()

                    if merge_batch_log_obj.batch_sub_action_name == 'MERGE':
                        if merge_batch_log_obj:
                            merge_batch_log_obj.batch_qty_stockout += total_formers_all
                            merge_batch_log_obj.batch_qty_in_wh -= total_formers_all
                            merge_batch_log_obj.batch_basket_qty_stockout += total_baskets_all
                            merge_batch_log_obj.batch_basket_qty_in_wh -= total_baskets_all
                            merge_batch_log_obj.save()

                        merge_batch_obj = Former_batch_data.objects.filter(batch_no=merge_batch_log_obj.batch_no).first()
                        if merge_batch_obj:
                            merge_batch_obj.batch_total_basket_in_wh -= total_baskets_all
                            merge_batch_obj.batch_total_former_in_wh -= total_formers_all
                            merge_batch_obj.save()


                    elif merge_batch_log_obj.batch_sub_action_name == 'SPLIT':
                        old_merge_batch_log_obj = Former_batch_data_log.objects.filter(batch_sub_action_key=key, batch_sub_action_name='MERGE', batch_action_name=action).first()

                        old_merge_batch_log_obj_batch_qty_merge = old_merge_batch_log_obj.batch_qty_merge
                        old_merge_batch_log_obj_batch_qty_stockout = old_merge_batch_log_obj.batch_qty_stockout
                        old_merge_batch_log_obj_batch_qty_total = old_merge_batch_log_obj.batch_qty_total
                        old_merge_batch_log_obj_batch_qty_in_wh = old_merge_batch_log_obj.batch_qty_in_wh

                        old_merge_batch_log_obj_batch_basket_qty_merge = old_merge_batch_log_obj.batch_basket_qty_merge
                        old_merge_batch_log_obj_batch_basket_qty_stockout = old_merge_batch_log_obj.batch_basket_qty_stockout
                        old_merge_batch_log_obj_batch_basket_qty_total = old_merge_batch_log_obj.batch_basket_qty_total
                        old_merge_batch_log_obj_batch_basket_qty_in_wh = old_merge_batch_log_obj.batch_basket_qty_in_wh


                        if old_merge_batch_log_obj:
                            old_merge_batch_log_obj.batch_combine = batch_no
                            old_merge_batch_log_obj.batch_qty_merge = 0
                            old_merge_batch_log_obj.batch_qty_split = -old_merge_batch_log_obj.batch_qty_stockout
                            old_merge_batch_log_obj.batch_qty_total = old_merge_batch_log_obj.batch_qty_total - old_merge_batch_log_obj_batch_qty_merge - old_merge_batch_log_obj_batch_qty_stockout
                            old_merge_batch_log_obj.batch_basket_qty_merge = 0
                            old_merge_batch_log_obj.batch_basket_qty_split = -old_merge_batch_log_obj.batch_basket_qty_stockout
                            old_merge_batch_log_obj.batch_basket_qty_total = old_merge_batch_log_obj.batch_basket_qty_total - old_merge_batch_log_obj_batch_basket_qty_merge - old_merge_batch_log_obj_batch_basket_qty_stockout
                            old_merge_batch_log_obj.batch_sub_action_name = 'SPLIT'
                            old_merge_batch_log_obj.save()

                        old_merge_batch_obj = Former_batch_data.objects.filter(batch_no=old_merge_batch_log_obj.batch_no).first()
                        if old_merge_batch_obj:
                            old_merge_batch_obj.batch_total_former = old_merge_batch_log_obj.batch_qty_total
                            old_merge_batch_obj.batch_total_basket = old_merge_batch_log_obj.batch_basket_qty_total
                            old_merge_batch_obj.save()

                        new_merge_batch_log_obj = Former_batch_data_log.objects.filter(batch_no=batch_no, batch_sub_action_key=key, batch_sub_action_name='SPLIT', batch_action_name=action).first()
                        if new_merge_batch_log_obj:
                            new_merge_batch_log_obj.batch_combine = ''

                            new_merge_batch_log_obj.batch_qty_merge = old_merge_batch_log_obj_batch_qty_total - old_merge_batch_log_obj_batch_qty_in_wh - new_merge_batch_log_obj.batch_qty_stockout
                            new_merge_batch_log_obj.batch_qty_stockout = new_merge_batch_log_obj.batch_qty_stockout + total_formers_all
                            new_merge_batch_log_obj.batch_qty_split = 0
                            new_merge_batch_log_obj.batch_qty_in_wh = new_merge_batch_log_obj.batch_qty_in_wh - total_formers_all
                            new_merge_batch_log_obj.batch_qty_total = new_merge_batch_log_obj.batch_qty_stockout + new_merge_batch_log_obj.batch_qty_in_wh + new_merge_batch_log_obj.batch_qty_merge

                            new_merge_batch_log_obj.batch_basket_qty_merge = old_merge_batch_log_obj_batch_basket_qty_total - old_merge_batch_log_obj_batch_basket_qty_in_wh - new_merge_batch_log_obj.batch_basket_qty_stockout
                            new_merge_batch_log_obj.batch_basket_qty_stockout = new_merge_batch_log_obj.batch_basket_qty_stockout + total_baskets_all
                            new_merge_batch_log_obj.batch_basket_qty_split = 0
                            new_merge_batch_log_obj.batch_basket_qty_in_wh = new_merge_batch_log_obj.batch_basket_qty_in_wh - total_baskets_all
                            new_merge_batch_log_obj.batch_basket_qty_total = new_merge_batch_log_obj.batch_basket_qty_stockout + new_merge_batch_log_obj.batch_basket_qty_in_wh + new_merge_batch_log_obj.batch_basket_qty_merge

                            new_merge_batch_log_obj.batch_sub_action_name = 'MERGE'
                            new_merge_batch_log_obj.save()

                            new_merge_batch_obj = Former_batch_data.objects.filter(batch_no=new_merge_batch_log_obj.batch_no).first()
                            if new_merge_batch_obj:
                                new_merge_batch_obj.batch_total_basket_in_wh = new_merge_batch_log_obj.batch_basket_qty_in_wh
                                new_merge_batch_obj.batch_total_former_in_wh = new_merge_batch_log_obj.batch_qty_in_wh
                                new_merge_batch_obj.save()



                        new_merge_batch_obj = Former_batch_data.objects.filter(batch_no=batch_no).first()
                        if new_merge_batch_obj:
                            new_merge_batch_obj.batch_total_former = new_merge_batch_log_obj.batch_qty_total
                            new_merge_batch_obj.batch_total_basket = new_merge_batch_log_obj.batch_basket_qty_total
                            new_merge_batch_obj.save()

                        get_other_batch_list = Former_batch_data_log.objects.filter(batch_sub_action_key=key, batch_action_name=action).exclude(batch_no__in=[old_merge_batch_obj.batch_no, new_merge_batch_obj.batch_no])
                        if get_other_batch_list.exists():
                            for other_batch in get_other_batch_list:
                                other_batch.batch_combine = batch_no
                                other_batch.save()

                else:
                    const_final_used_day = final_used_day

                    final_used_day = (
                        Former_batch_data.objects
                            .filter(batch_no=batch_no)
                            .values_list('former_used_day', flat=True)
                            .first()
                    )

                    final_used_day = final_used_day if final_used_day is not None else const_final_used_day
                    old_merge_batch_log_obj = Former_batch_data_log.objects.filter(batch_sub_action_key=key, batch_sub_action_name='MERGE', batch_action_name=action).first()

                    old_merge_batch_log_obj_batch_qty_merge = old_merge_batch_log_obj.batch_qty_merge
                    old_merge_batch_log_obj_batch_qty_stockout = old_merge_batch_log_obj.batch_qty_stockout
                    old_merge_batch_log_obj_batch_qty_total = old_merge_batch_log_obj.batch_qty_total
                    old_merge_batch_log_obj_batch_qty_in_wh = old_merge_batch_log_obj.batch_qty_in_wh

                    old_merge_batch_log_obj_batch_basket_qty_merge = old_merge_batch_log_obj.batch_basket_qty_merge
                    old_merge_batch_log_obj_batch_basket_qty_stockout = old_merge_batch_log_obj.batch_basket_qty_stockout
                    old_merge_batch_log_obj_batch_basket_qty_total = old_merge_batch_log_obj.batch_basket_qty_total
                    old_merge_batch_log_obj_batch_basket_qty_in_wh = old_merge_batch_log_obj.batch_basket_qty_in_wh


                    if old_merge_batch_log_obj:
                        old_merge_batch_log_obj.batch_combine = batch_no

                        old_merge_batch_log_obj.batch_qty_merge = 0
                        old_merge_batch_log_obj.batch_qty_split = -old_merge_batch_log_obj.batch_qty_stockout
                        old_merge_batch_log_obj.batch_qty_total = old_merge_batch_log_obj.batch_qty_total - old_merge_batch_log_obj_batch_qty_merge - old_merge_batch_log_obj_batch_qty_stockout

                        old_merge_batch_log_obj.batch_basket_qty_merge = 0
                        old_merge_batch_log_obj.batch_basket_qty_split = -old_merge_batch_log_obj.batch_basket_qty_stockout
                        old_merge_batch_log_obj.batch_basket_qty_total = old_merge_batch_log_obj.batch_basket_qty_total - old_merge_batch_log_obj_batch_basket_qty_merge - old_merge_batch_log_obj_batch_basket_qty_stockout
                        old_merge_batch_log_obj.batch_sub_action_name = 'SPLIT'

                        old_merge_batch_log_obj.save()



                    old_merge_batch_obj = Former_batch_data.objects.filter(batch_no=old_merge_batch_log_obj.batch_no).first()
                    if old_merge_batch_obj:
                        old_merge_batch_obj.batch_total_former = old_merge_batch_log_obj.batch_qty_total
                        old_merge_batch_obj.batch_total_basket = old_merge_batch_log_obj.batch_basket_qty_total
                        old_merge_batch_obj.save()

                    Former_batch_data_log.objects.create(
                        batch_no=batch_no,
                        batch_action_name=action,

                        batch_qty_stockout=total_formers_all,
                        batch_qty_merge=old_merge_batch_log_obj_batch_qty_total - old_merge_batch_log_obj_batch_qty_in_wh,
                        batch_qty_in_wh=original_former_qty - total_formers_all,
                        batch_qty_total=original_former_qty + old_merge_batch_log_obj_batch_qty_total - old_merge_batch_log_obj_batch_qty_in_wh,

                        batch_basket_qty_stockout=total_baskets_all,
                        batch_basket_qty_merge=old_merge_batch_log_obj_batch_basket_qty_total - old_merge_batch_log_obj_batch_basket_qty_in_wh,
                        batch_basket_qty_in_wh=original_basket_qty - total_baskets_all,
                        batch_basket_qty_total=original_basket_qty + old_merge_batch_log_obj_batch_basket_qty_total - old_merge_batch_log_obj_batch_basket_qty_in_wh,

                        batch_used_day=final_used_day,
                        batch_sub_action_name='MERGE',
                        batch_sub_action_key=key
                    )

                    Former_batch_data.objects.filter(batch_no=batch_no).update(
                        batch_total_basket=original_basket_qty + old_merge_batch_log_obj_batch_basket_qty_total - old_merge_batch_log_obj_batch_basket_qty_in_wh,
                        batch_total_former=original_former_qty + old_merge_batch_log_obj_batch_qty_total - old_merge_batch_log_obj_batch_qty_in_wh,
                        batch_total_basket_in_wh=original_basket_qty - total_baskets_all,
                        batch_total_former_in_wh=original_former_qty - total_formers_all,
                        former_used_day=final_used_day,
                        update_by=user,
                        update_at=timezone.now()
                    )

                    get_other_batch_list = Former_batch_data_log.objects.filter(batch_sub_action_key=key, batch_action_name=action).exclude(batch_no__in=[old_merge_batch_obj.batch_no, batch_no])
                    if get_other_batch_list.exists():
                        for other_batch in get_other_batch_list:
                            other_batch.batch_combine = batch_no
                            other_batch.save()
