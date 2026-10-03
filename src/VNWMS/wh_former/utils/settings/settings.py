from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.http import HttpResponse, JsonResponse, HttpRequest
from django.shortcuts import redirect
from django.urls import reverse

from wh_former.forms import ManageSettingForm, ManageVendorDataForm
from wh_former.models import Parameter_data, RFID_setting
from wh_former.utils.rfid.uhf import rfid_test_connection, rfid_start_stop



@login_required
def manage_setting(request):
    all_vendors = []
    all_params = []
    settings_list = RFID_setting.objects.all().order_by('-update_at')

    if request.method == 'POST':
        # form_type = request.POST.get('form_type')
        # if form_type == 'vendor':
        #     vendor_form = ManageVendorDataForm(request.POST, prefix='vendor')
        #     if vendor_form.is_valid():
        #         obj = vendor_form.save(commit=False)
        #         if not obj.pk:
        #             obj.create_by = request.user
        #         obj.update_by = request.user
        #         obj.save()
        #
        # elif form_type == 'param':
        #     params_form = ManageParameterDataForm(request.POST, prefix='param')
        #     if params_form.is_valid():
        #         obj = params_form.save(commit=False)
        #         if not obj.pk:
        #             obj.create_by = request.user
        #         obj.update_by = request.user
        #         obj.save()
        #
        # active_section = form_type
        pass

    else:
        # vendor_form = ManageVendorDataForm(prefix='vendor')
        # params_form = ManageParameterDataForm(prefix='param')
        pass

    return render(request,'wh_former/components/settings/settings.html', locals())




@login_required
def manage_setting_device_add_new(request):
    settings_list = RFID_setting.objects.all().order_by('-update_at')
    return render(request, 'wh_former/components/settings/settings.html', locals())

from django.db import transaction

@login_required
@csrf_exempt
def manage_add_new_client(request):
    if request.method == 'POST':
        form = ManageSettingForm(request.POST)
        if form.is_valid():
            rfid_ip = form.cleaned_data['rfid_reader_ip']
            port = form.cleaned_data['rfid_reader_port']
            client_ip = form.cleaned_data['client_device_ip']
            qs = RFID_setting.objects.filter(rfid_reader_ip=rfid_ip, rfid_reader_port=port)
            if form.instance.pk:
                qs = qs.exclude(pk=form.instance.pk)

            if qs.exists():
                return JsonResponse({'status': 'duplicate'})
            else:
                with transaction.atomic():
                    existed = RFID_setting.objects.filter(client_device_ip=client_ip, is_control=True).exists()

                    setting = form.save(commit=False)
                    setting.create_by = request.user
                    setting.update_by = request.user

                    if not existed:
                        setting.is_control = True

                    setting.save()
                row_html = render_to_string(
                    'wh_former/components/settings/manage_setting_client_list.html', {'s': setting})
                return JsonResponse({'status': 'ok', 'row': row_html, 'redirect_url': reverse('manage_wh_former_index')})
        else:
            return JsonResponse({'status': 'invalid', 'errors': form.errors})
    else:
        form = ManageSettingForm()
        return render(request, 'wh_former/components/settings/manage_setting_add_new.html', locals())


@login_required
def manage_edit_client(request, id):
    setting = get_object_or_404(RFID_setting, pk=id)
    if request.method == 'POST':
        form = ManageSettingForm(request.POST, instance=setting)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.update_by = request.user
            updated.save()
            return JsonResponse({'status': 'ok', 'redirect_url': reverse('manage_wh_former_index')})
        else:
            return JsonResponse({'status': 'invalid', 'errors': form.errors})
    else:
        form = ManageSettingForm(instance=setting)
        return render(request, 'wh_former/components/settings/manage_setting_add_new.html', locals())


@csrf_exempt
def manage_connection_test_client(request, id):
    try:
        setting = RFID_setting.objects.get(id=id, is_control=True)
        success = rfid_test_connection(setting.rfid_reader_ip, setting.rfid_reader_port)
        return HttpResponse("✔️ Success" if success else "❌ Failed", content_type="text/plain")
    except:
        return HttpResponse("❌ Error", content_type="text/plain")


@require_POST
def manage_power_client(request, id):
    try:
        setting = RFID_setting.objects.get(id=id, is_control=True)
        setting.rfid_reader_status = not setting.rfid_reader_status
        if not setting.rfid_reader_status:
            setting.rfid_reader_state = False
        setting.update_by = request.user
        setting.save()
    except RFID_setting.DoesNotExist:
        pass
    return redirect('manage_wh_former_index')


@require_POST
def manage_rfid_power_read(request, id, field):
    try:
        setting = RFID_setting.objects.get(id=id, is_control=True)
        if field == "status":
            setting.rfid_reader_status = not setting.rfid_reader_status
            if not setting.rfid_reader_status:
                setting.rfid_reader_state = False
        elif field == "action":
            if setting.rfid_reader_status:
                setting.rfid_reader_state = not setting.rfid_reader_state
                fake_request = HttpRequest()
                fake_request.method = "POST"
                rfid_start_stop(fake_request, id, request.user)
        setting.update_by = request.user
        setting.save()
    except RFID_setting.DoesNotExist:
        pass
    return redirect('manage_wh_former_index')


from django.utils import timezone
@login_required
def manage_delete_client(request, id):
    setting = get_object_or_404(RFID_setting, pk=id)
    client_ip = setting.client_device_ip
    was_active = setting.is_control

    with transaction.atomic():
        client_qs = (RFID_setting.objects
                     .select_for_update()
                     .filter(client_device_ip=client_ip))

        setting.delete()

        if was_active:
            candidate = (client_qs
                         .order_by('-create_at', '-pk')
                         .first())

            if candidate:
                now = timezone.now()
                client_qs.update(is_control=False, update_at=now)

                candidate.is_control = True
                candidate.rfid_reader_state = True
                candidate.update_at = now
                candidate.save(update_fields=['is_control', 'rfid_reader_state', 'update_at'])

    return redirect('manage_wh_former_index')



@login_required
def update_control_location(request):
    if request.method == "POST":
        loc = request.POST.get("location_name")
        client_ip = request.META.get("REMOTE_ADDR")
        now = timezone.now()

        with transaction.atomic():
            RFID_setting.objects.filter(client_device_ip=client_ip, is_control=True).update(is_control=False, update_at=now)

            setting = RFID_setting.objects.filter(client_device_ip=client_ip, location_name=loc).first()
            if setting:
                setting.is_control = True
                setting.rfid_reader_state = False
                setting.update_at = now
                setting.save(update_fields=["is_control", "rfid_reader_state", "update_at"])

        return redirect(request.META.get("HTTP_REFERER", "manage_wh_former_index"))