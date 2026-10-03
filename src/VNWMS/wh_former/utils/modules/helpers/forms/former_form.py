from wh_former.models import Former_batch_data, Former_master_data_scan_log
from wh_former.forms import FormerMasterDataForm
from django.utils.translation import ugettext_lazy as _

def convert_display_to_original(value):
    if not value:
        return ''
    
    surface_mapping = {
        str(_('Standard Fine Surface')): 'Standard Fine Surface',
        str(_('Standard Coarse Surface')): 'Standard Coarse Surface', 
        str(_('Standard Diamond Textured')): 'Standard Diamond Textured',
        str(_('Energy-saving Fine Surface')): 'Energy-saving Fine Surface'
    }
    
    type_mapping = {
        str(_('Stainless steel')): 'Stainless steel',
        str(_('Ceramic')): 'Ceramic'
    }
    
    if str(value) in surface_mapping:
        return surface_mapping[str(value)]
    elif str(value) in type_mapping:
        return type_mapping[str(value)]

    return str(value)

def get_former_batch_data_table(batch_no):
    batch_obj = Former_batch_data.objects.get(batch_no=batch_no)

    former_receive_form = batch_obj.former_receive_form or ''
    former_size = batch_obj.former_size or ''
    former_vendor = batch_obj.former_vendor or ''
    batch_data_date = batch_obj.batch_data_date.strftime('%Y-%m-%d') if batch_obj.batch_data_date else ''
    former_surface = batch_obj.former_surface or ''
    former_length = str(batch_obj.former_length) if batch_obj.former_length else ''
    former_type = batch_obj.former_type or ''
    former_purchase_order = batch_obj.former_purchase_order or ''
    former_item_no = batch_obj.former_item_no or ''
    former_used_day = str(batch_obj.former_used_day) if batch_obj.former_used_day else '0'
    batch_no = batch_obj.batch_no or ''

    form_data = {
        'batch_no': batch_no,
        'former_receive_form': former_receive_form,
        'former_vendor': former_vendor,
        'batch_data_date': batch_data_date,
        'former_surface': former_surface,
        'former_length': former_length,
        'former_type': former_type,
        'former_purchase_order': former_purchase_order,
        'former_item_no': former_item_no,
        'former_used_day': former_used_day,
        'former_aql': batch_obj.former_aql or 1.0,
    }

    return former_receive_form, former_size, former_vendor, batch_data_date, former_surface, former_length, former_type, \
           former_purchase_order, former_item_no, former_used_day, batch_no, form_data


def get_former_batch_data_request(request):
    former_receive_form = request.POST.get('former_receive_form', '') if request.method == 'POST' else ''
    former_size = request.POST.get('params_size', '') if request.method == 'POST' else ''
    former_vendor = request.POST.get('vendor_name', '') if request.method == 'POST' else ''
    batch_data_date = request.POST.get('batch_data_date', '') if request.method == 'POST' else ''
    former_surface = convert_display_to_original(request.POST.get('params_surface', '')) if request.method == 'POST' else ''
    former_length = request.POST.get('length_value', '') if request.method == 'POST' else ''
    former_type = convert_display_to_original(request.POST.get('params_type', '')) if request.method == 'POST' else ''
    former_purchase_order = request.POST.get('former_purchase_order', '') if request.method == 'POST' else ''
    former_item_no = request.POST.get('item_no', '') if request.method == 'POST' else ''
    former_used_day = request.POST.get('former_used_day', '0') if request.method == 'POST' else '0'
    batch_no = request.POST.get('batch_no', '') if request.method == 'POST' else ''

    return former_receive_form, former_size, former_vendor, batch_data_date, former_surface, former_length, former_type, \
           former_purchase_order, former_item_no, former_used_day, batch_no



def get_former_batch_data_request_as_dict(request):
    former_receive_form = request.POST.get('former_receive_form', '') if request.method == 'POST' else ''
    former_vendor = request.POST.get('vendor_name', '') if request.method == 'POST' else ''
    batch_data_date = request.POST.get('batch_data_date', '') if request.method == 'POST' else ''
    former_surface = convert_display_to_original(request.POST.get('params_surface', '')) if request.method == 'POST' else ''
    former_length = request.POST.get('length_value', '') if request.method == 'POST' else ''
    former_type = convert_display_to_original(request.POST.get('params_type', '')) if request.method == 'POST' else ''
    former_purchase_order = request.POST.get('former_purchase_order', '') if request.method == 'POST' else ''
    former_item_no = request.POST.get('item_no', '') if request.method == 'POST' else ''
    former_used_day = request.POST.get('former_used_day', '0') if request.method == 'POST' else '0'
    batch_no = request.POST.get('batch_no', '') if request.method == 'POST' else ''
    former_aql = request.POST.get('former_aql', '1.0') if request.method == 'POST' else '1.0'

    return {
        'former_receive_form': former_receive_form,
        'former_vendor': former_vendor,
        'batch_data_date': batch_data_date,
        'former_surface': former_surface,
        'former_length': former_length,
        'former_type': former_type,
        'former_purchase_order': former_purchase_order,
        'former_item_no': former_item_no,
        'former_used_day': former_used_day,
        'batch_no': batch_no,
        'former_aql': former_aql,
    }




def get_former_batch_data(request, existing_temp=None):
    if existing_temp and existing_temp.batch_no:
        return get_former_batch_data_table(existing_temp.batch_no)
    else:
        data = get_former_batch_data_request(request)
        return data + (None,)


def handle_form_input_log(batch_no, former_receive_form, former_item_no, former_used_day, former_purchase_order,
                          batch_data_date, former_vendor, former_type, former_surface, former_size, length_value):
    obj, created = Former_master_data_scan_log.objects.update_or_create(
        batch_dn=former_receive_form,
        batch_item_no=former_item_no,
        batch_used_day=former_used_day,
        batch_purchase_order=former_purchase_order,
        batch_data_date=batch_data_date,
        batch_former_vendor=former_vendor,
        batch_former_type=former_type,
        batch_former_surface=former_surface,
        batch_former_size=former_size,
        batch_former_length=length_value,
        batch_no=batch_no,
        defaults={
            "batch_purchase_received": 0,
        }
    )
    return obj, created


def handle_former_master_data_form(request, batch_no, former_size, former_vendor, former_item_no, length_value,
                                   former_surface, former_type, former_receive_form, former_used_day,
                                   former_purchase_order, batch_data_date):
    try:
        batch_no_obj = Former_batch_data.objects.get(batch_no=batch_no)
        return batch_no_obj, True, None

    except Former_batch_data.DoesNotExist:
        form = FormerMasterDataForm(request.POST)

        if form.is_valid():
            batch_no_obj = form.save(commit=False)
            batch_no_obj.create_by = request.user
            batch_no_obj.former_size = former_size
            batch_no_obj.former_vendor = former_vendor
            batch_no_obj.group_batch = batch_no.split("-")[0]
            batch_no_obj.former_surface = convert_display_to_original(former_surface)
            batch_no_obj.former_type = convert_display_to_original(former_type)
            batch_no_obj.former_length = length_value
            batch_no_obj.former_item_no = former_item_no
            batch_no_obj.update_by = request.user
            batch_no_obj.save()

            handle_form_input_log(batch_no, former_receive_form, former_item_no, former_used_day, former_purchase_order,
                                  batch_data_date, former_vendor, former_type, former_surface, former_size,
                                  length_value)
            return batch_no_obj, True, None
        else:
            return None, False, f"{form.errors}"


def reset_former_master_data_form():
    return {
        'form': FormerMasterDataForm(),
        'former_receive_form': '',
        'former_size': '',
        'former_vendor': '',
        'batch_data_date': '',
        'former_surface': '',
        'former_length': '',
        'former_type': '',
        'former_purchase_order': '',
        'former_item_no': '',
        'former_used_day': '0',
        'batch_no': '',
        'rack_stocked': 0,
        'enable_save_button': False
    }


def handle_reset_former_master_data_form(success, error_message=None):
    if success:
        return True, False, reset_former_master_data_form()
    else:
        return False, True, {'error_message': error_message}


def handle_former_search_query():
    return (Former_batch_data.objects.filter(is_active=True, batch_total_basket__gt=0, batch_total_former__gt=0).only(
        'former_vendor', 'former_type', 'former_item_no', 'former_receive_form', 'former_size', 'former_length',
        'former_used_day',
        'batch_no', 'create_at', 'is_active', 'batch_total_basket', 'batch_total_former', 'batch_data_date',
        'batch_last_stockout').
     order_by('former_size', 'former_used_day', 'former_type', 'batch_total_former'))



def handle_former_search_form(request):
    former_vendor = request.GET.get('vendor_name', '')
    former_item_no = request.GET.get('item_no', '')
    former_size = request.GET.get('params_size', '')
    former_length = request.GET.get('length_value', '')
    former_surface = request.GET.get('params_surface', '')
    former_type = request.GET.get('params_type', '')

    return former_vendor, former_item_no, former_size, former_length, former_surface, former_type


def handle_former_search_filter(queryset, form, former_vendor, former_item_no, former_size, former_length, former_surface, former_type):
    filters = {
        'former_vendor__icontains': former_vendor,
        'former_surface__icontains': former_surface,
        'former_type__icontains': former_type,
        'former_item_no__icontains': former_item_no,
        'former_receive_form__icontains': form.cleaned_data.get('former_receive_form'),
        'former_size__icontains': former_size,
        'former_length': former_length,
        'batch_no__icontains': form.cleaned_data.get('batch_no'),
    }
    queryset = queryset.filter(**{k: v for k, v in filters.items() if v})

    used_day_val = form.cleaned_data.get('former_used_day', '').strip()
    if used_day_val:
        import re
        m = re.match(r'^(<=|>=|=|<|>)?(\d+)$', used_day_val)
        if m:
            op = m.group(1) or '='
            num = m.group(2)
            if op == '=':
                queryset = queryset.filter(former_used_day=int(num))
            elif op == '>=':
                queryset = queryset.filter(former_used_day__gte=int(num))
            elif op == '<=':
                queryset = queryset.filter(former_used_day__lte=int(num))
            elif op == '>':
                queryset = queryset.filter(former_used_day__gt=int(num))
            elif op == '<':
                queryset = queryset.filter(former_used_day__lt=int(num))

    return queryset


def handle_former_search_result(queryset, column_width, column_align, results):
    for i, row in enumerate(queryset, start=1):
        row_data = list(zip([
            i,
            row.batch_no or '',
            row.former_receive_form or '',
            row.former_size or '',
            row.former_vendor or '',
            row.former_length or '',
            _(row.former_type) or '',
            row.former_item_no or '',
            row.create_at.strftime('%d/%m/%Y') if row.create_at else '',
            row.former_used_day,
            row.batch_total_basket or '',
            row.batch_total_former or '',
            '',
        ], column_width, column_align))

        results.append((row_data, row.is_active))

    return results


def get_former_stockout_data(existing_temp):
    if not existing_temp or not existing_temp.batch_no:
        return '', '', '', ''
    
    try:
        batch_data = Former_batch_data.objects.filter(
            batch_no=existing_temp.batch_no
        ).values('former_size').first()
        
        size = batch_data['former_size'] if batch_data else ''
        machine = existing_temp.to_bin or ''
        plant = machine[:3] if machine and len(machine) >= 3 else ''

        # from wh_former.models import Former_stockout_form
        # stockout_form_obj = Former_stockout_form.objects.filter(
        #     stockout_to=machine
        # ).values('stockout_form').first()
        #
        # stockout_form = stockout_form_obj['stockout_form'] if stockout_form_obj else ''
        stockout_form = existing_temp.stock_form

        return size, machine, plant, stockout_form
        
    except Exception as e:
        print(f"Error in get_former_stockout_data: {e}")
        return '', '', '', ''


def get_former_stockout_data_as_dict(existing_temp):
    size, machine, plant, stockout_form = get_former_stockout_data(existing_temp)
    return {
        'params_size': size,
        'selected_machine': machine,
        'selected_plant': plant,
        'stockout_form': stockout_form
    }


def clean_former_master_data_form():
    former_receive_form = former_size = former_vendor = batch_data_date = former_surface = length_value =\
        former_type = former_purchase_order = former_item_no = former_used_day = batch_no = form_data = ''
    return former_receive_form, former_size, former_vendor, batch_data_date, former_surface, length_value, former_type,\
           former_purchase_order, former_item_no, former_used_day, batch_no, form_data


def show_noti_modal(request, is_form_restored, action):
    show_process_warning = False
    if is_form_restored and request.method == 'GET':
        referer = request.META.get('HTTP_REFERER', '')
        current_path = request.path
        if referer and not referer.endswith(current_path):
            show_process_warning = True
        else:
            if action == 'STOU':
                if referer and referer.endswith(current_path):
                    show_process_warning = True

    return show_process_warning
