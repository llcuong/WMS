from wh_former.models import Basket_master_data, Basket_master_data_log, Basket_master_data_print_log, Former_bin_data
from django.db.models import OuterRef, Subquery, CharField, IntegerField

from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from datetime import datetime, date
import concurrent.futures
import math
from django.db import connection
import time

def get_basket_series(fact_code, basket_receive_date):
    prefix = f'{fact_code}{datetime.strptime(basket_receive_date, "%Y-%m-%d").strftime("%y%m%d")}'

    latest_log = Basket_master_data_log.objects.filter(
        basket_no__basket_no__startswith=f"{prefix}"
    ).order_by('-basket_series').first()

    next_series = latest_log.basket_series + 1 if latest_log else 1
    return prefix, next_series


def get_basket_no(fact_code):
    prefix, series = get_basket_series(fact_code)
    return f"{prefix}" + f"{series:06d}"


def get_basket_master(queryset, column_width, column_align, save_times):
    results = []
    for i, row in enumerate(queryset, start=1):
        row_data = list(zip([
            i,
            row.basket_no,
            row.basket_vendor or '',
            row.basket_capacity or '',
            row.basket_length or '',
            row.basket_receive_date.strftime('%d/%m/%Y') if row.basket_receive_date else '',
            row.basket_purchase_order or '',
            save_times or '',
        ], column_width, column_align))

        results.append((row_data, True))
    return results


def basket_master_data_form_data_split(data, n):
    k, m = divmod(len(data), n)
    return [data[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]


def basket_master_data_create(args_batch):
    results = []
    for args in args_batch:
        results.append(basket_master_data_create_task(args))
    return results


def basket_master_data_create_task(args):
    (basket_no, basket_vendor, basket_capacity, basket_receive_qty, basket_length,
     basket_receive_date, basket_purchase_order, create_by, basket_description,
     basket_series, save_times) = args

    new_basket = Basket_master_data.objects.create(
        basket_no=basket_no,
        basket_vendor=basket_vendor,
        basket_capacity=basket_capacity,
        basket_receive_qty=basket_receive_qty,
        basket_length=basket_length,
        basket_receive_date=basket_receive_date,
        basket_purchase_order=basket_purchase_order,
        create_by=create_by,
        # is_print=1 #New added to test - fuckyou
    )

    Basket_master_data_log.objects.create(
        basket_no=new_basket,
        basket_series=basket_series,
        basket_description=basket_description,
        saved=save_times
    )

    new_basket.basket_series = basket_series

    # New added to test - fuckyou
    # f_name = 'FNB431240142'
    # b_name = 'D21-2'
    # sql = f"""
    #         INSERT INTO [GDWMS].[dbo].[wh_former_former_bin_data] (
    #         [bin],
    #         [basket_former_qty],
    #         [basket_no],
    #         [batch_no],
    #         [to_bin_key],
    #         [update_at]
    #     )
    #     VALUES (
    #         '{b_name}', 5, '{basket_no}', '{f_name}', '', GETDATE()
    #     );
    #
    # """
    # vnwms_db = vnwms_database().execute_sql(sql)
    # New added to test - fuckyou

    return new_basket



def extract_basket_form_data(request, form):
    basket_length = request.POST.get('length_value', '')
    basket_vendor = request.POST.get('vendor_name', '')
    fact_code = request.POST.get('plant_code', '')
    basket_description = request.POST.get('basket_description', '')

    basket_receive_qty = int(request.POST.get('basket_receive_qty', 0))
    basket_receive_date = request.POST.get('basket_receive_date', str(datetime.today().date()))
    basket_capacity = (int(request.POST.get('basket_capacity', 0)))
    basket_purchase_order = request.POST.get('basket_purchase_order', '')

    save_times = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        if not form.is_valid():
            success = False
            msg = form.errors
        else:
            success = True
            msg = ''
        return success, msg, (basket_length, basket_vendor, fact_code,
               basket_description, basket_receive_qty, basket_receive_date, basket_capacity, basket_purchase_order, save_times)
    except Exception as e:
        return False, e, []



def handle_basket_master_data_form(request, form, column_width, column_align):
    try:
        success, msg, data = extract_basket_form_data(request, form)
        (basket_length, basket_vendor, fact_code,
         basket_description, basket_receive_qty, basket_receive_date, basket_capacity,
         basket_purchase_order, save_times) = data
        if success:
            request.session['save_times'] = save_times
            request.session.modified = True

            prefix, start_series = get_basket_series(fact_code, basket_receive_date)
            total_baskets = basket_receive_qty
            queryset = []


            #New added to test - fuckyou
            #
            #
            # f_name = 'FNB431240142'
            # d_name = '184421045'
            # sql = f"""
            # INSERT INTO [GDWMS].[dbo].[wh_former_former_batch_data] (
            #     [batch_no],
            #     [former_receive_form],
            #     [former_size],
            #     [former_vendor],
            #     [former_type],
            #     [former_purchase_order],
            #     [former_surface],
            #     [former_length],
            #     [former_used_day],
            #     [former_item_no],
            #     [former_aql],
            #     [is_active],
            #     [batch_data_date],
            #     [batch_last_stockout],
            #     [batch_total_basket],
            #     [batch_total_former],
            #     [create_at],
            #     [update_at],
            #     [create_by_id],
            #     [update_by_id],
            #     [group_batch],
            #     [batch_total_basket_in_wh],
            #     [batch_total_former_in_wh]
            # )
            # VALUES (
            # '{f_name}', '{d_name}', 'S', 'Shinko', 'Ceramic', {total_baskets*5}, 'Standard Fine Surface', 380, 0, 'FNA38122',
            # 1, 1, '2025-09-26', '', {total_baskets}, {total_baskets*5}, GETDATE(), GETDATE(),  12, 12, '{f_name}', {total_baskets}, {total_baskets*5});
            #
            #
            #
            # INSERT INTO [GDWMS].[dbo].[wh_former_former_batch_data_log] (
            #     [batch_no],
            #     [batch_action_name],
            #     [batch_qty_split],
            #     [batch_qty_total],
            #     [batch_qty_in_wh],
            #     [batch_used_day],
            #     [batch_change_day],
            #     [batch_stockout_to],
            #     [batch_combine],
            #     [batch_sub_action_key],
            #     [batch_sub_action_name],
            #     [batch_qty_merge],
            #     [batch_qty_stockout],
            #     [batch_basket_qty_in_wh],
            #     [batch_basket_qty_merge],
            #     [batch_basket_qty_split],
            #     [batch_basket_qty_stockout],
            #     [batch_basket_qty_total],
            #     [create_at],
            #     [update_at],
            #     [batch_basket_qty_stockin],
            #     [batch_qty_stockin]
            # )
            # VALUES (
            #     '{f_name}',  'CRTE',  0, {total_baskets*5}, {total_baskets*5}, 0, '2025-09-26', NULL, NULL,  NULL, NULL,
            #     {total_baskets*5}, 0, {total_baskets}, {total_baskets}, 0, 0, {total_baskets}, GETDATE(), GETDATE(),  {total_baskets}, {total_baskets*5}
            # );
            #
            # """
            #
            # vnwms_db = vnwms_database().execute_sql(sql)
            #New added to test - fuckyou


            args_list = []
            for i in range(total_baskets):
                basket_series = start_series + i
                basket_no = f"{prefix}{basket_series:06d}"
                args_list.append((
                    basket_no, basket_vendor, basket_capacity, basket_receive_qty, basket_length,
                    form.cleaned_data.get('basket_receive_date'),
                    form.cleaned_data.get('basket_purchase_order', ''),
                    request.user, basket_description, basket_series, save_times
                ))

            num_threads = min(10, len(args_list))
            chunked_args = basket_master_data_form_data_split(args_list, num_threads)

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                batch_results = list(executor.map(basket_master_data_create, chunked_args))

            for batch in batch_results:
                queryset.extend(batch)

            results = get_basket_master(queryset, column_width, column_align, save_times)

            Basket_master_data_print_log.objects.update_or_create(
                defaults={
                    'basket_printed_qty': 0,
                    'basket_created_qty': total_baskets,
                },
                basket_purchase_order=basket_purchase_order,
                basket_vendor=basket_vendor,
                basket_receive_date=form.cleaned_data.get('basket_receive_date'),
                plant_code=fact_code,
                basket_receive_qty=basket_receive_qty,
                basket_length=basket_length,
                saved=save_times,
            )

            return results, len(results), None, True, basket_length, basket_vendor

        return [], 0, msg, False, basket_length, basket_vendor
    except Exception as e:
        return [], 0, str(e), False, 0, ''


def handle_basket_search_query():
    # latest_log = Basket_master_data_log.objects.filter(basket_no=OuterRef('basket_no')).order_by('-basket_no')
    # bin_data = Former_bin_data.objects.filter(basket_no=OuterRef('basket_no')).select_related('batch_no')
    #
    # queryset = Basket_master_data.objects.select_related('create_by').annotate(
    #     basket_description=Subquery(latest_log.values('basket_description')[:1], output_field=CharField()),
    #     basket_stockin_date=Subquery(latest_log.values('basket_stockin_date')[:1], output_field=CharField()),
    #     saved=Subquery(latest_log.values('saved')[:1], output_field=CharField()),
    #     batch_no=Subquery(bin_data.values('batch_no__batch_no')[:1], output_field=CharField()),
    #     bin=Subquery(bin_data.values('bin')[:1], output_field=CharField()),
    #     basket_former_qty=Subquery(bin_data.values('basket_former_qty')[:1], output_field=IntegerField()),
    # ).order_by('-basket_receive_date')
    base_sql = """
            SELECT bmd.*, bmdl.basket_series, bmdl.saved, 
                   bmdl.basket_description, bmdl.basket_stockin_date,
                   fbd.batch_no, fbd.bin, fbd.basket_former_qty
            FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
            LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                ON bmd.basket_no = bmdl.basket_no
            LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] fbd
                ON bmd.basket_no = fbd.basket_no
            """
    return base_sql


def check_for_active_groups(queryset, search_filter):
    """
    Check status of groups based on is_print and is_active values
    Returns:
    - 0: No printed baskets or no data
    - 1: Has printed baskets but all are inactive (is_print > 0 and is_active = 0)
    - 2: Has printed baskets with some still active (is_print > 0 and is_active = 1)
    """
    if search_filter != 'key':
        return 0

    checked_groups = set()

    for row in queryset:
        saved_value = getattr(row, 'saved', '')
        if saved_value and saved_value not in checked_groups:
            checked_groups.add(saved_value)

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_count,
                        SUM(CASE WHEN bmd.is_print > 0 AND bmd.is_active = 0 THEN 1 ELSE 0 END) as printed_inactive_count,
                        SUM(CASE WHEN bmd.is_print > 0 AND bmd.is_active = 1 THEN 1 ELSE 0 END) as printed_active_count
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    WHERE bmdl.saved = %s
                """, [saved_value])

                result = cursor.fetchone()
                if result:
                    printed_inactive_count = result[1] or 0
                    printed_active_count = result[2] or 0

                    if printed_active_count > 0:
                        return 2

                    if printed_inactive_count > 0:
                        return 1

    return 0


def handle_basket_search_form(form, base_queryset, column_width, column_align, default_filter):
    vendor_name = ''
    try:
        search_filter = form.cleaned_data.get('search_filter') if form.cleaned_data.get('search_filter') else default_filter
        basket_no = form.cleaned_data.get('basket_no')
        basket_vendor = form.cleaned_data.get('vendor_name')
        basket_receive_date = form.cleaned_data.get('basket_receive_date')
        saved_group = form.cleaned_data.get('saved_group')
        purchase_order = form.cleaned_data.get('purchase_order')

        conditions = []
        params = []
        has_conditions = any([basket_no, basket_vendor, basket_receive_date, saved_group, purchase_order])

        if search_filter == 'all':
            if not has_conditions:
                # sql = """
                # WITH LatestSaved AS (
                #     SELECT MAX(saved) as max_saved
                #     FROM [GDWMS].[dbo].[wh_former_basket_master_data_log]
                # ),
                # FilteredData AS (
                #     SELECT bmd.*, bmdl.basket_series, bmdl.saved,
                #            bmdl.basket_description, bmdl.basket_stockin_date,
                #            fbd.batch_no, fbd.bin, fbd.basket_former_qty
                #     FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                #     LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                #         ON bmd.basket_no = bmdl.basket_no
                #     LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] fbd
                #         ON bmd.basket_no = fbd.basket_no
                #     CROSS JOIN LatestSaved ls
                #     WHERE bmdl.saved = ls.max_saved
                # )
                # SELECT * FROM FilteredData
                # ORDER BY basket_no DESC
                # """

                # sql = """
                #     SELECT
                #         bmd.*,
                #         bmdl.basket_series,
                #         bmdl.saved,
                #         bmdl.basket_description,
                #         bmdl.basket_stockin_date,
                #         fbd.batch_no,
                #         fbd.bin,
                #         fbd.basket_former_qty
                #     FROM [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
                #     LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] AS bmdl
                #         ON bmd.basket_no = bmdl.basket_no
                #     LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
                #         ON bmd.basket_no = fbd.basket_no
                #     WHERE
                #         bmd.basket_receive_date >= DATEADD(DAY, -10, CAST(GETDATE() AS date))
                #         AND bmd.basket_purchase_order IS NOT NULL
                #     ORDER BY
                #         bmd.basket_purchase_order;
                # """

                sql = """
                SELECT TOP (1000)
                    bmd.*,
                    bmdl.basket_series,
                    bmdl.saved,
                    bmdl.basket_description,
                    bmdl.basket_stockin_date,
                    fbd.batch_no,
                    fbd.bin,
                    fbd.basket_former_qty
                FROM [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
                LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] AS bmdl
                    ON bmd.basket_no = bmdl.basket_no
                LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
                    ON bmd.basket_no = fbd.basket_no
                ORDER BY 
                    bmd.basket_receive_date DESC;

                """
            else:
                sql = base_queryset
                if basket_no and len(basket_no) >= 8:
                    if len(basket_no) >= 15:
                        conditions.append("bmd.basket_no = %s")
                        params.append(basket_no)
                    else:
                        conditions.append("bmd.basket_no LIKE %s")
                        params.append(f"{basket_no}%")

                if basket_vendor:
                    conditions.append("bmd.basket_vendor = %s")
                    params.append(basket_vendor)
                    vendor_name = basket_vendor

                if basket_receive_date:
                    conditions.append("bmd.basket_receive_date = %s")
                    params.append(basket_receive_date)

                if saved_group:
                    conditions.append("bmdl.saved = %s")
                    params.append(saved_group)

                if purchase_order:
                    conditions.append("bmd.purchase_order = %s")
                    params.append(purchase_order)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                sql += " ORDER BY bmd.basket_no"

        elif search_filter == 'key':
            if len(basket_no) > 15:
                sql = """
                WITH BasketSaved AS (
                    SELECT saved 
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data_log]
                    WHERE basket_no = %s
                ),
                FilteredData AS (
                    SELECT bmd.*, bmdl.basket_series, bmdl.saved, 
                           bmdl.basket_description, bmdl.basket_stockin_date,
                           fbd.batch_no, fbd.bin, fbd.basket_former_qty
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] fbd
                        ON bmd.basket_no = fbd.basket_no
                    INNER JOIN BasketSaved bs ON bmdl.saved = bs.saved
                )
                SELECT * FROM FilteredData
                ORDER BY basket_no DESC
                """
                params = [basket_no]
            elif saved_group:
                if purchase_order:
                    sql = """
                        SELECT 
                            bmd.*, 
                            bmdl.basket_series, 
                            bmdl.saved, 
                            bmdl.basket_description, 
                            bmdl.basket_stockin_date,
                            fbd.batch_no, 
                            fbd.bin, 
                            fbd.basket_former_qty
                        FROM [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
                        LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] AS bmdl
                            ON bmd.basket_no = bmdl.basket_no
                        LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
                            ON bmd.basket_no = fbd.basket_no
                        WHERE bmdl.saved = %s
                              and bmd.basket_purchase_order = %s
                        ORDER BY bmd.basket_no DESC;
                    """
                    params = [saved_group, purchase_order]
                else:
                    sql = """
                        SELECT 
                            bmd.*, 
                            bmdl.basket_series, 
                            bmdl.saved, 
                            bmdl.basket_description, 
                            bmdl.basket_stockin_date,
                            fbd.batch_no, 
                            fbd.bin, 
                            fbd.basket_former_qty
                        FROM [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
                        LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] AS bmdl
                            ON bmd.basket_no = bmdl.basket_no
                        LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
                            ON bmd.basket_no = fbd.basket_no
                        WHERE bmdl.saved = %s
                        ORDER BY bmd.basket_no DESC;
                    """
                    params = [saved_group]

            elif purchase_order:
                sql = """
                    SELECT 
                        bmd.*, 
                        bmdl.basket_series, 
                        bmdl.saved, 
                        bmdl.basket_description, 
                        bmdl.basket_stockin_date,
                        fbd.batch_no, 
                        fbd.bin, 
                        fbd.basket_former_qty
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] AS bmd
                    LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] AS bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] AS fbd
                        ON bmd.basket_no = fbd.basket_no
                    WHERE bmd.basket_purchase_order = %s
                    ORDER BY bmd.basket_no DESC;
                """
                params = [purchase_order]
            else:
                return [], 0, None, True, vendor_name, {}, 2

        else:
            status_map = {
                'active': 1,
                'disable': 0,
                'scrap': 3,
                'unknown': 2
            }

            if search_filter in status_map:
                status_value = status_map[search_filter]

                if has_conditions:
                    sql = base_queryset
                    conditions.append("bmd.is_active = %s")
                    params.append(status_value)

                    if basket_no and len(basket_no) >= 8:
                        if len(basket_no) >= 15:
                            conditions.append("bmd.basket_no = %s")
                            params.append(basket_no)
                        else:
                            conditions.append("bmd.basket_no LIKE %s")
                            params.append(f"{basket_no}%")

                    if basket_vendor:
                        conditions.append("bmd.basket_vendor = %s")
                        params.append(basket_vendor)
                        vendor_name = basket_vendor

                    if basket_receive_date:
                        conditions.append("bmd.basket_receive_date = %s")
                        params.append(basket_receive_date)

                    if saved_group:
                        conditions.append("bmdl.saved = %s")
                        params.append(saved_group)

                    if purchase_order:
                        conditions.append("bmd.purchase_order = %s")
                        params.append(purchase_order)

                    sql += " WHERE " + " AND ".join(conditions)
                    sql += " ORDER BY bmd.basket_no DESC"

                else:
                    sql = f"""
                    SELECT TOP 1000 bmd.*, bmdl.basket_series, bmdl.saved, 
                           bmdl.basket_description, bmdl.basket_stockin_date,
                           fbd.batch_no, fbd.bin, fbd.basket_former_qty
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    LEFT JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    LEFT JOIN [GDWMS].[dbo].[wh_former_former_bin_data] fbd
                        ON bmd.basket_no = fbd.basket_no
                    WHERE bmd.is_active = %s
                    ORDER BY bmd.basket_no DESC
                    """
                    params = [status_value]

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            raw_results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        class QueryResult:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        queryset_objects = [QueryResult(row) for row in raw_results]

        if search_filter == 'key':
            results = get_basket_search_with_key_actions(queryset_objects, column_width, column_align, search_filter)
            editable_groups = get_editable_groups_info(queryset_objects, search_filter, basket_no, saved_group, purchase_order)
            
            has_active_groups = check_for_active_groups(queryset_objects, search_filter)
            if has_active_groups == 2:
                error_msg = _('Atleast 1 basket in thís group already IN USE, can not edit anymore')
                return results, len(results), error_msg, False, vendor_name, editable_groups, has_active_groups
        else:
            results = get_basket_search(queryset_objects, column_width, column_align)
            editable_groups = {}

        return results, len(results), None, True, vendor_name, editable_groups, 2

    except Exception as e:
        return [], 0, str(e), False, vendor_name, {}, 2





def get_basket_search(queryset, column_width, column_align):
    """Modified version of get_basket_search to work with raw query results"""
    results = []

    for i, row in enumerate(queryset, start=1):
        is_active = getattr(row, 'is_active', 0)
        is_print  = getattr(row, 'is_print', 0)
        if is_active == 1:
            action_html = mark_safe(f'''
                 <button type="button" class="btn btn-sm btn-outline-primary" style="width: 40px; height: 40px"
                     onclick="openBasketModal('{row.basket_no}', 
                     '{getattr(row, 'basket_vendor', '')}', '{getattr(row, 'basket_receive_date', '')}', 
                     '{getattr(row, 'basket_capacity', '')}', '{getattr(row, 'create_at', '')}', 
                     '{getattr(row, 'basket_description', '')}')">
                         <i class="fas fa-print" style="font-size: 18px"></i>
                 </button>
             ''')

            status_html = mark_safe(f'''
                 <div style="position: relative; border: none; padding-top: 2px;">
                     <span style="background-color: #28a745; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("In use")}</span>
                 </div>
             ''')
        else:
            action_html = mark_safe(f'''
                 <button type="button" class="btn btn-sm btn-outline-secondary"
                         style="width: 40px; height: 40px; background-color: transparent; border: none;"
                         disabled>
                     <i class="fas fa-ban" style="font-size: 18px;"></i>
                 </button>
             ''')

            if is_active == 0:
                status_html = mark_safe(f'''
                     <div style="position: relative; border: none; padding-top: 2px;">
                         <span style="background-color: #2272F4; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("Active")}</span>
                     </div>
                 ''')
            elif is_active == 2:
                status_html = mark_safe(f'''
                     <div style="position: relative; border: none; padding-top: 2px;">
                         <span style="background-color: #ffc107; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("Unknown")}</span>
                     </div>
                 ''')
            elif is_active == 3:
                status_html = mark_safe(f'''
                     <div style="position: relative; border: none; padding-top: 2px;">
                         <span style="background-color: #dc3545; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("Scrap")}</span>
                     </div>
                 ''')
        create_at = getattr(row, 'create_at', None)
        basket_receive_date = getattr(row, 'basket_receive_date', None)

        days_diff = 0
        if create_at:
            if isinstance(create_at, str):
                try:
                    create_date = datetime.strptime(create_at.split()[0], '%Y-%m-%d').date()
                    days_diff = (date.today() - create_date).days
                except:
                    days_diff = 0
            else:
                days_diff = (date.today() - create_at.date()).days

        receive_date_str = '-'
        if basket_receive_date:
            if isinstance(basket_receive_date, str):
                try:
                    receive_date_str = datetime.strptime(basket_receive_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                except:
                    receive_date_str = basket_receive_date
            else:
                receive_date_str = basket_receive_date.strftime('%d/%m/%Y')

        row_data = list(zip([
            i,
            getattr(row, 'basket_no', '-'),
            getattr(row, 'basket_purchase_order', None) or '-',
            getattr(row, 'saved', None) or '-',
            f"{days_diff} " + _('days') if create_at else '-',
            getattr(row, 'former_size', None) or '-',
            getattr(row, 'bin', None) or '-',
            getattr(row, 'basket_vendor', None) or '-',
            getattr(row, 'basket_capacity', None) or '-',
            receive_date_str,
            getattr(row, 'batch_no', None) or '-',
            getattr(row, 'basket_former_qty', None) or '-',
            is_print,
            status_html,
            action_html,
            getattr(row, 'basket_description', None) or '-',
        ], column_width, column_align))

        results.append((row_data, is_active == 1))

    return results


def get_basket_search_with_key_actions(queryset, column_width, column_align, search_filter):
    results = []
    
    group_status = {}
    editable_groups = {}
    
    for row in queryset:
        saved_value = getattr(row, 'saved', '')

        if saved_value and saved_value not in group_status:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as total_count,
                           SUM(CASE WHEN bmd.is_active = 0 THEN 1 ELSE 0 END) as inactive_count
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    WHERE bmdl.saved = %s
                """, [saved_value])

                result = cursor.fetchone()
                if result and result[0] > 0:
                    can_edit = result[0] == result[1]
                    group_status[saved_value] = can_edit
                    
                    if can_edit and saved_value not in editable_groups:
                        basket_receive_date = getattr(row, 'basket_receive_date', '')
                        if basket_receive_date:
                            if isinstance(basket_receive_date, str):
                                try:
                                    basket_receive_date = datetime.strptime(basket_receive_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                                except:
                                    pass
                            elif hasattr(basket_receive_date, 'strftime'):
                                # Handle date object from database
                                basket_receive_date = basket_receive_date.strftime('%Y-%m-%d')
                        
                        editable_groups[saved_value] = {
                            'basket_no': getattr(row, 'basket_no', ''),
                            'basket_receive_date': basket_receive_date,
                            'basket_length': getattr(row, 'basket_length', '') or '',
                            'basket_purchase_order': getattr(row, 'basket_purchase_order', '') or '',
                            'basket_description': getattr(row, 'basket_description', '') or ''
                        }

    for i, row in enumerate(queryset, start=1):
        is_active = getattr(row, 'is_active', 0)
        saved_value = getattr(row, 'saved', '')
        is_print  = getattr(row, 'is_print', 0)

        if search_filter == 'key':
            action_html = mark_safe('<span>-</span>')
        else:
            if is_active == 1:
                action_html = mark_safe(f'''
                     <button type="button" class="btn btn-sm btn-outline-primary" style="width: 40px; height: 40px"
                         onclick="openBasketModal('{getattr(row, 'basket_no', '')}', 
                         '{getattr(row, 'basket_vendor', '')}', '{getattr(row, 'basket_receive_date', '')}', 
                         '{getattr(row, 'basket_capacity', '')}', '{getattr(row, 'create_at', '')}', 
                         '{getattr(row, 'basket_description', '')}')">
                             <i class="fas fa-pen" style="font-size: 18px"></i>
                     </button>
                 ''')
            else:
                action_html = mark_safe(f'''
                     <button type="button" class="btn btn-sm btn-outline-secondary"
                             style="width: 40px; height: 40px; background-color: transparent; border: none;"
                             disabled>
                         <i class="fas fa-ban" style="font-size: 18px;"></i>
                     </button>
                 ''')

        if is_active == 1:
            status_html = mark_safe(f'''
                 <div style="position: relative; border: none; padding-top: 2px;">
                     <span style="background-color: #28a745; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("In use")}</span>
                 </div>
             ''')
        elif is_active == 0:
            status_html = mark_safe(f'''
                 <div style="position: relative; border: none; padding-top: 2px;">
                     <span style="background-color: #2272F4; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("Active")}</span>
                 </div>
             ''')
        elif is_active == 2:
            status_html = mark_safe(f'''
                 <div style="position: relative; border: none; padding-top: 2px;">
                     <span style="background-color: #ffc107; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("Unknown")}</span>
                 </div>
             ''')
        else:
            status_html = mark_safe(f'''
                 <div style="position: relative; border: none; padding-top: 2px;">
                     <span style="background-color: #dc3545; border-radius: 16px; padding: 4px 12px; color: white; font-size: 13px;">{_("Scrap")}</span>
                 </div>
             ''')

        create_at = getattr(row, 'create_at', None)
        basket_receive_date = getattr(row, 'basket_receive_date', None)

        days_diff = 0
        if create_at:
            if isinstance(create_at, str):
                try:
                    create_date = datetime.strptime(create_at.split()[0], '%Y-%m-%d').date()
                    days_diff = (date.today() - create_date).days
                except:
                    days_diff = 0
            else:
                days_diff = (date.today() - create_at.date()).days

        receive_date_str = '-'
        if basket_receive_date:
            if isinstance(basket_receive_date, str):
                try:
                    receive_date_str = datetime.strptime(basket_receive_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                except:
                    receive_date_str = basket_receive_date
            else:
                receive_date_str = basket_receive_date.strftime('%d/%m/%Y')

        row_data = list(zip([
            i,
            getattr(row, 'basket_no', '-'),
            getattr(row, 'basket_purchase_order', None) or '-',
            getattr(row, 'saved', None) or '-',
            f"{days_diff} " + _('days') if create_at else '-',
            getattr(row, 'former_size', None) or '-',
            getattr(row, 'bin', None) or '-',
            getattr(row, 'basket_vendor', None) or '-',
            getattr(row, 'basket_capacity', None) or '-',
            receive_date_str,
            getattr(row, 'batch_no', None) or '-',
            getattr(row, 'basket_former_qty', None) or '-',
            is_print,
            status_html,
            action_html,
            getattr(row, 'basket_description', None) or '-',
        ], column_width, column_align))

        results.append((row_data, is_active == 1))

    return results


def get_editable_groups_info(queryset, search_filter, basket_no, saved_group, purchase_order):
    """
    Get information about editable groups for key search filter
    Returns dictionary with editable group information
    """
    if search_filter != 'key':
        return {}
    
    editable_groups = {}

    for row in queryset:
        purchase_order = getattr(row, 'basket_purchase_order', '')

        if purchase_order and purchase_order not in editable_groups:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as total_count,
                           SUM(CASE WHEN bmd.is_active = 0 THEN 1 ELSE 0 END) as inactive_count
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    WHERE bmd.basket_purchase_order = %s
                """, [purchase_order])

                result = cursor.fetchone()
                # if result and result[0] > 0:
                if result:
                    # can_edit = result[0] == result[1]
                    can_edit = True

                    if can_edit:
                        basket_receive_date = getattr(row, 'basket_receive_date', '')
                        if basket_receive_date:
                            if isinstance(basket_receive_date, str):
                                try:
                                    basket_receive_date = datetime.strptime(basket_receive_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                                except:
                                    pass
                            elif hasattr(basket_receive_date, 'strftime'):
                                basket_receive_date = basket_receive_date.strftime('%Y-%m-%d')

                        editable_groups[purchase_order] = {
                            'basket_no': getattr(row, 'basket_no', ''),
                            'basket_receive_date': basket_receive_date,
                            'basket_length': getattr(row, 'basket_length', '') or '',
                            'basket_vendor': getattr(row, 'basket_vendor', '') or '',
                            'basket_purchase_order': getattr(row, 'basket_purchase_order', '') or '',
                            'basket_description': getattr(row, 'basket_description', '') or ''
                        }
    
    return editable_groups


def handle_basket_edit_form(request):
    """Handle basket edit form submission"""
    try:
        basket_no = request.POST.get('edit_basket_no')
        basket_receive_date = request.POST.get('edit_basket_receive_date')
        basket_length = request.POST.get('length_value')
        basket_purchase_order = request.POST.get('edit_basket_purchase_order')
        basket_description = request.POST.get('edit_basket_description')
        basket_vendor = request.POST.get('vendor_name')
        saved_value = request.POST.get('edit_saved_value')
        action_type = request.POST.get('action_type')

        # with connection.cursor() as cursor:
        #     cursor.execute("""
        #         SELECT COUNT(*) as total_count,
        #                SUM(CASE WHEN bmd.is_active = 0 THEN 1 ELSE 0 END) as inactive_count
        #         FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
        #         INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
        #             ON bmd.basket_no = bmdl.basket_no
        #         WHERE bmdl.saved = %s
        #     """, [saved_value])
        #
        #     result = cursor.fetchone()
        #     if not result or result[0] == 0 or result[0] != result[1]:
        #         return False, "Cannot edit: Some baskets in this group are active"

        if action_type == 'delete':
            with connection.cursor() as cursor:
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM [GDWMS].[dbo].[wh_former_basket_master_data_log]
                        WHERE saved = %s
                    """, [saved_value])
                    delete_count = cursor.fetchone()[0]

                    cursor.execute("""
                        SELECT bmd.basket_no 
                        FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                        INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                            ON bmd.basket_no = bmdl.basket_no
                        WHERE bmdl.saved = %s
                    """, [saved_value])
                    basket_nos = [row[0] for row in cursor.fetchall()]

                    if basket_nos:
                        placeholders = ','.join(['%s'] * len(basket_nos))
                        cursor.execute(f"""
                            DELETE FROM [GDWMS].[dbo].[wh_former_former_bin_data]
                            WHERE basket_no IN ({placeholders})
                        """, basket_nos)

                    cursor.execute("""
                        DELETE FROM [GDWMS].[dbo].[wh_former_basket_master_data_log]
                        WHERE saved = %s
                    """, [saved_value])

                    if basket_nos:
                        placeholders = ','.join(['%s'] * len(basket_nos))
                        cursor.execute(f"""
                            DELETE FROM [GDWMS].[dbo].[wh_former_basket_master_data]
                            WHERE basket_no IN ({placeholders})
                        """, basket_nos)

                    return True, f"Successfully deleted {delete_count} baskets from group"

                except Exception as e:
                    return False, f"Error deleting baskets: {str(e)}"
        elif action_type == 'update':
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    WHERE bmd.basket_purchase_order = %s
                """, [basket_purchase_order])
                update_count = cursor.fetchone()[0]

                update_fields = []
                params = []

                if basket_receive_date:
                    update_fields.append("basket_receive_date = %s")
                    params.append(basket_receive_date)

                if basket_length:
                    update_fields.append("basket_length = %s")
                    params.append(basket_length)

                if basket_purchase_order:
                    update_fields.append("basket_purchase_order = %s")
                    params.append(basket_purchase_order)

                if basket_vendor:
                    update_fields.append("basket_vendor = %s")
                    params.append(basket_vendor)

                if update_fields:
                    params.append(saved_value)
                    cursor.execute(f"""
                        UPDATE bmd SET {', '.join(update_fields)}
                        FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                        INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                            ON bmd.basket_no = bmdl.basket_no
                        WHERE bmd.basket_purchase_order = %s
                    """, params)

                if basket_description:
                    if len(saved_value) == 14:
                        cursor.execute("""
                            UPDATE [GDWMS].[dbo].[wh_former_basket_master_data_log]
                            SET basket_description = %s
                            WHERE saved = %s
                        """, [basket_description, saved_value])
                    else:
                        cursor.execute("""
                            UPDATE bmdl SET bmdl.basket_description = %s
                            FROM [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                            JOIN [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                            ON bmdl.basket_no = bmd.basket_no
                            WHERE bmd.basket_purchase_order = %s
                        """, [basket_description, basket_purchase_order])

            return True, f"Successfully updated {update_count} baskets in group"

    except Exception as e:
        return False, str(e)

    return False, "Invalid action"


def clear_baskets_by_save_times(save_times):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                    SELECT bmd.basket_no 
                    FROM [GDWMS].[dbo].[wh_former_basket_master_data] bmd
                    INNER JOIN [GDWMS].[dbo].[wh_former_basket_master_data_log] bmdl
                        ON bmd.basket_no = bmdl.basket_no
                    WHERE bmdl.saved = %s AND bmd.is_print = 0
                """, [save_times])

            basket_numbers = [row[0] for row in cursor.fetchall()]

            if not basket_numbers:
                return 0, []

            basket_placeholders = ','.join(['%s'] * len(basket_numbers))

            cursor.execute(f"""
                    DELETE FROM [GDWMS].[dbo].[wh_former_former_bin_data]
                    WHERE basket_no IN ({basket_placeholders})
                """, basket_numbers)

            cursor.execute(f"""
                    DELETE FROM [GDWMS].[dbo].[wh_former_basket_master_data_log]
                    WHERE basket_no IN ({basket_placeholders})
                """, basket_numbers)

            cursor.execute(f"""
                    DELETE FROM [GDWMS].[dbo].[wh_former_basket_master_data]
                    WHERE basket_no IN ({basket_placeholders}) AND is_print = 0
                """, basket_numbers)

            return len(basket_numbers), basket_numbers

    except Exception as e:
        raise Exception(f"Error deleting baskets: {str(e)}")

