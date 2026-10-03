from django.views.decorators.http import require_POST
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect

from wh_former.models import RFID_setting, RFID_read_log, RFID_read

from wh_former.utils.rfid.uhf import start_reader, stop_reader
from wh_former.utils.modules.helpers.permissions.control_permission import get_client_ip, get_controller_ip

import json


def mark_rfid_data_as_passed(rfid_reader_ip, pid):
    """
    Helper function để đánh dấu tất cả RFID data là đã passed
    """
    try:
        RFID_read_log.objects.filter(
            rfid_reader_ip=rfid_reader_ip, 
            pid=pid, 
            is_passed=False
        ).update(is_passed=True)
        
        RFID_read.objects.filter(
            rfid_reader_ip=rfid_reader_ip, 
            pid=pid, 
            is_passed=False
        ).update(is_passed=True)
        
        return True
    except Exception as e:
        print(f"Error marking RFID data as passed: {e}")
        return False


@require_POST
def rfid_start_reader_api(request, id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    
    client_ip = get_client_ip(request)
    pid = int(request.GET.get("pid", 1))
    #
    # # Lấy thêm dữ liệu từ POST body
    # id_stockout_form = request.POST.get("id_stockout_form", "")
    # id_stock_form_input = request.POST.get("id_stock_form_input", "")
    # vb
    try:
        setting = RFID_setting.objects.get(id=id, is_control=True)

        print(f"rfid_start_reader_api -> setting -> {setting.rfid_reader_ip}")
        if str(setting.client_device_ip) != str(client_ip):
            return redirect(request.META.get('HTTP_REFERER', 'manage_wh_former_index'))

        if setting.rfid_reader_status and not setting.rfid_reader_state:
            mark_rfid_data_as_passed(setting.rfid_reader_ip, pid)

            fake_request = HttpRequest()
            fake_request.method = "POST"
            fake_request.POST = request.POST.copy()
            
            success = start_reader(fake_request, id, request.user, pid)
            if success:
                setting.rfid_reader_state = True
                setting.save()
                
                # Log hoặc xử lý thêm với id_stockout_form và id_stock_form_input

                return HttpResponse("OK")
            else:
                return HttpResponseBadRequest("Unable to start reader")
        else:
            return HttpResponseBadRequest("Reader already running or not available")

    except RFID_setting.DoesNotExist:
        return HttpResponseBadRequest("Invalid RFID Setting ID")


@require_POST
def rfid_stop_reader_api(request, id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    
    pid = int(request.GET.get("pid", 1))
    
    try:
        setting = RFID_setting.objects.get(id=id)
        if setting.rfid_reader_status and setting.rfid_reader_state:
            mark_rfid_data_as_passed(setting.rfid_reader_ip, pid)
            
            fake_request = HttpRequest()
            fake_request.method = "POST"
            success = stop_reader(fake_request, id)
            if success:
                setting.rfid_reader_state = False
                setting.save()
                return HttpResponse("OK")
            else:
                return HttpResponseBadRequest("Unable to stop reader")
        else:
            return HttpResponseBadRequest("Reader not running")
            
    except RFID_setting.DoesNotExist:
        return HttpResponseBadRequest("Invalid RFID Setting ID")


@require_POST
def rfid_clear_reader_api(request):
    pid = int(request.POST.get("pid", 1))
    rfid_reader_ip = get_controller_ip(get_client_ip(request))
    
    try:
        epcs_json = request.POST.get("epcs", "[]")
        epcs = json.loads(epcs_json)

        mark_rfid_data_as_passed(rfid_reader_ip, pid)
        
        return JsonResponse({"status": "ok", "message": "RFID data cleared successfully"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})


@require_POST
def rfid_cleanup_on_page_exit_api(request):
    """
    API để cleanup RFID data khi thoát khỏi trang
    """
    pid = int(request.POST.get("pid", 1))
    rfid_reader_ip = get_controller_ip(get_client_ip(request))
    
    try:
        # Đánh dấu tất cả RFID data là đã passed
        mark_rfid_data_as_passed(rfid_reader_ip, pid)
        
        # Tìm và stop reader nếu đang chạy
        try:
            settings = RFID_setting.objects.filter(
                rfid_reader_ip=rfid_reader_ip,
                rfid_reader_state=True
            )
            
            for setting in settings:
                fake_request = HttpRequest()
                fake_request.method = "POST"
                stop_reader(fake_request, setting.id)
                setting.rfid_reader_state = False
                setting.save()
                
        except Exception as e:
            print(f"Error stopping readers on page exit: {e}")
        
        return JsonResponse({"status": "ok", "message": "Cleanup completed"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})



