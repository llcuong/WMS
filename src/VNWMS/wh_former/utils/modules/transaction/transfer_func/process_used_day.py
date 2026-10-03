from wh_former.models import Former_stockout_form

from datetime import datetime

def _used_day(operation_type, form_name, batch_no_obj, former_used_day, action):
    # if operation_type == 'stockin':
    #     if form_name:
    #         stockout_query = Former_stockout_form.objects.filter(stockout_form=form_name).values_list('stockout_date').first()
    #         if stockout_query:
    #             day_diff = (datetime.today().date() - stockout_query[0]).days
    #             return former_used_day + day_diff
    #         else:
    #             return former_used_day
    #     else:
    #         return former_used_day
    #
    # elif operation_type == 'stockout':
    #     return batch_no_obj.former_used_day
    return former_used_day
