from django.shortcuts import render
from wh_former.models import RFID_setting


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_controller_ip(client_device_ip):
    controller_ip = RFID_setting.objects.filter(client_device_ip=client_device_ip, is_control=True).values_list('rfid_reader_ip',
                                                                                               flat=True).first()
    return controller_ip


def get_permission(request):
    client_ip = get_client_ip(request)
    pid = int(request.GET.get("pid", 1))
    is_ip_allowed = RFID_setting.objects.filter(client_device_ip=client_ip, is_control=True).exists()

    if request.user.is_superuser:
        setting = RFID_setting.objects.filter(client_device_ip=client_ip, is_control=True).first()
        if setting:
            return client_ip, pid, setting.rfid_reader_state, setting.id, setting.location_name, setting.rfid_reader_ip, is_ip_allowed
        else:
            first_setting = RFID_setting.objects.first()
            if not first_setting:
                return render(request, 'wh_former/modules/components/errors/404.html', status=404)

            return first_setting.client_device_ip, pid, first_setting.rfid_reader_state, \
                   first_setting.id, first_setting.location_name, first_setting.rfid_reader_ip, is_ip_allowed
    try:
        setting = RFID_setting.objects.filter(client_device_ip=client_ip, is_control=True).first()
        return client_ip, pid, setting.rfid_reader_state, setting.id, setting.location_name, setting.rfid_reader_ip, is_ip_allowed
    except RFID_setting.DoesNotExist:
        return render(request, 'wh_former/modules/components/errors/403.html', status=403)
