from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

from wh_former.models import RFID_setting, RFID_read_log, RFID_read, Former_bin_data, Former_stockout_form, Former_batch_data, Former_rack_bin_temp

from wh_former.utils.helpers.epc_helpers import get_former_master_data
from wh_former.utils.modules.helpers.permissions.control_permission import get_client_ip, get_controller_ip
from wh_former.utils.rfid.printer import net_print_and_write_list

from datetime import date
import json

FIXED_PRINTER_IP = "172.18.51.231"

@login_required
@require_POST
@csrf_exempt
def rfid_print_api(request):
    try:
        payload = json.loads(request.body)
        epc_list = payload.get("epc_list")
        batch_size = payload.get("batch_size", len(epc_list))
        start_index = payload.get("start_index", 0)

        if not isinstance(epc_list, list) or not epc_list:
            return HttpResponseBadRequest("Payload must include a non-empty list 'epc_list'")

        # Lấy batch hiện tại để in
        end_index = min(start_index + batch_size, len(epc_list))
        current_batch = epc_list[start_index:end_index]

        results = net_print_and_write_list(current_batch, current_batch, FIXED_PRINTER_IP)
        return JsonResponse({
            "status": "ok",
            "printed": len(current_batch),
            "results": results,
            "total_items": len(epc_list),
            "current_batch_size": len(current_batch),
            "start_index": start_index,
            "end_index": end_index,
            "has_more": end_index < len(epc_list)
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# @login_required
# @require_POST
# @csrf_exempt
# def rfid_print_api(request):
#     try:
#         payload = json.loads(request.body)
#         epc_list = payload.get("epc_list")
#         batch_size = payload.get("batch_size", len(epc_list))  # Thêm batch_size parameter
#         start_index = payload.get("start_index", 0)  # Thêm start_index parameter
#         current_batch_number = payload.get("current_batch_number", 0)
#         is_final_batch = False
#
#         if not isinstance(epc_list, list) or not epc_list:
#             return HttpResponseBadRequest("Payload must include a non-empty list 'epc_list'")
#
#         # Lấy batch hiện tại để in
#         end_index = min(start_index + batch_size +1, len(epc_list)+1)
#         # print(f'end_index --> {end_index}')
#         total = 0
#         for i in range(is_final_batch+1):
#             if i == 0:
#                 total += 1
#             elif i == 1:
#                 total += 5
#             else:
#                 total += 50
#
#         if total >= len(epc_list):
#             is_final_batch = True
#
#
#         # if current_batch_number == 0:
#         #     if is_final_batch:
#         #         current_epc_list = epc_list[start_index:end_index] + ['-']
#         #         current_label_list = ['-'] + epc_list[start_index:end_index]
#         #     else:
#         #         current_epc_list = epc_list[start_index:end_index]
#         #         current_label_list = epc_list[start_index+1:end_index+1]
#         # else:
#         #     if is_final_batch:
#         #         current_epc_list = epc_list[start_index:end_index] + ['-']
#         #         current_label_list = epc_list[start_index+1:end_index]
#         #     else:
#         #         current_epc_list = epc_list[start_index:end_index] + ['-']
#         #         current_label_list = epc_list[start_index+1:end_index]
#
#         add_epc_list = epc_list + ['0']
#         add_label_list = [' '] + epc_list
#
#         current_epc_list = add_epc_list[start_index:end_index]
#         current_label_list = add_label_list[start_index:end_index]
#
#         # print(f'current_epc_list    -->>>> {current_epc_list}')
#         # print(f'current_label_list  -->>>> {current_label_list}')
#
#         results = net_print_and_write_list(current_label_list, current_epc_list, FIXED_PRINTER_IP)
#         return JsonResponse({
#             "status": "ok",
#             "printed": len(current_epc_list),
#             "results": results,
#             "total_items": len(epc_list),
#             "current_batch_size": len(current_epc_list),
#             "start_index": start_index,
#             "end_index": end_index,
#             "has_more": end_index < len(epc_list)
#         })
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)

# @require_GET
# def get_rfid_epc_api(request):
#     controller_ip = get_controller_ip(get_client_ip(request))
#     pid = request.GET.get("pid")
#     action = request.GET.get("action")
#     selected_machine = request.GET.get("selected_machine", '')
#     stock_form = request.GET.get("stock_form")
#
#     # 1) BASE = số bản ghi đã trả cho client, chưa pass
#     base = RFID_read_log.objects.filter(
#         rfid_reader_ip=controller_ip, pid=pid,
#         is_passed=False, is_logged=True
#     ).count()
#
#     # 2) CHỈ TRẢ CÁI CHƯA GỬI (is_logged=False), thứ tự tăng theo pk
#     latest_epc = RFID_read_log.objects.filter(
#         rfid_reader_ip=controller_ip, pid=pid,
#         is_passed=False, is_logged=False
#     ).order_by('pk')
#
#     data, epcs_to_update = [], []
#
#     try:
#         for index, epc in enumerate(latest_epc):
#             values = get_former_master_data(epc.basket_no, pid, selected_machine)
#             if not values:
#                 continue
#
#             # 3) ĐÁNH SỐ CỘNG DỒN
#             data.append({
#                 'count': base + index + 1,
#                 'epc_raw': values[0],
#                 'epc_vendor': values[2],
#                 'epc_qty': values[1],
#                 'bin': values[3],
#             })
#
#             # Đánh dấu đã gửi, để lần sau không trả lại
#             epc.is_logged = True
#             epcs_to_update.append(epc)
#
#             # Lưu lịch sử một lần cho mỗi log mới
#             RFID_read.objects.create(
#                 basket_no=values[0],
#                 rfid_reader_ip=controller_ip,
#                 pid=pid,
#                 create_by=request.user
#             )
#
#             # --- GIỮ NGUYÊN NHÁNH STOCKIN / STOCKOUT CỦA MÀY ---
#             if action in ("stockin", "stockout"):
#                 if action == "stockout":
#                     obj = Former_bin_data.objects.only('batch_no').filter(basket_no=values[0]).first()
#                     if obj:
#                         data[-1]["batch_no"] = [
#                             obj.batch_no.batch_no,
#                             obj.batch_no.former_aql,
#                             obj.batch_no.former_type,
#                             obj.batch_no.former_vendor,
#                             obj.batch_no.former_used_day,
#                             obj.batch_no.former_size,
#                             obj.batch_no.former_surface
#                         ]
#                     else:
#                         data[-1]["batch_no"] = ["-", "-", "-", "-", "-", "-", "-"]
#
#                 elif action == "stockin":
#                     if stock_form:
#                         try:
#                             stock_form_name = stock_form.split('(')[0].strip()
#                             if selected_machine != 'CLEAN':
#                                 stock_form_size = stock_form.split('(')[1].split(')')[0].strip()
#                                 stock_form_obj = Former_stockout_form.objects.filter(
#                                     stockout_form=stock_form_name,
#                                     former_size=stock_form_size
#                                 ).first()
#                             else:
#                                 stock_form_obj = Former_stockout_form.objects.filter(
#                                     stockout_form=stock_form_name,
#                                 ).first()
#                                 stock_form_size = Former_batch_data.objects.filter(
#                                     batch_no=stock_form_obj.batch_no
#                                 ).values_list('former_size', flat=True).first()
#
#                             if stock_form_obj and stock_form_obj.batch_no:
#                                 try:
#                                     batch_obj = Former_batch_data.objects.get(batch_no=stock_form_obj.batch_no)
#                                     if selected_machine == 'CLEAN':
#                                         new_used_day = stock_form_obj.most_batch_used_day
#                                     else:
#                                         days_diff = (date.today() - stock_form_obj.stockout_date).days
#                                         new_used_day = stock_form_obj.most_batch_used_day + days_diff + 10
#
#                                     data[-1]["batch_no"] = [
#                                         batch_obj.batch_no,
#                                         batch_obj.former_aql,
#                                         batch_obj.former_type,
#                                         batch_obj.former_vendor,
#                                         new_used_day,
#                                         stock_form_size,
#                                         batch_obj.former_surface,
#                                     ]
#
#                                 except Former_batch_data.DoesNotExist:
#                                     data[-1]["batch_no"] = [
#                                         f"RETURN_{stock_form_name}",
#                                         1.0, "RETURN",
#                                         stock_form_obj.stockout_from or "UNKNOWN",
#                                         stock_form_obj.most_batch_used_day,
#                                         stock_form_size,
#                                         '-'
#                                     ]
#                             else:
#                                 data[-1]["batch_no"] = ["-", "-", "NO_FORM", "-", "-", stock_form_size, "-"]
#                         except Exception as e:
#                             print(f"Error parsing stock_form: {e}")
#                             data[-1]["batch_no"] = ["-", "-", "ERROR", "-", "-", "-", "-"]
#                     else:
#                         obj = Former_bin_data.objects.only('batch_no').filter(basket_no=values[0]).first()
#                         if obj:
#                             data[-1]["batch_no"] = [
#                                 obj.batch_no.batch_no,
#                                 obj.batch_no.former_aql,
#                                 obj.batch_no.former_type,
#                                 obj.batch_no.former_vendor,
#                                 obj.batch_no.former_used_day,
#                                 obj.batch_no.former_size,
#                                 obj.batch_no.former_surface,
#                             ]
#                         else:
#                             data[-1]["batch_no"] = ["-", "-", "NEW", "-", "-", "-", "-"]
#
#         if epcs_to_update:
#             RFID_read_log.objects.bulk_update(epcs_to_update, ['is_logged'])
#
#     except Exception as e:
#         print(e)
#
#     return JsonResponse({'epcs': data})
#

@require_POST
def get_stockform_bin_api(request):
    """
    API để lấy bin từ stockform
    """
    stockform = request.POST.get("stockform", "")

    if not stockform:
        return JsonResponse({"error": "Stockform is required"}, status=400)

    try:
        stockout_form = Former_stockout_form.objects.filter(stockout_form=stockform).first()
        if stockout_form:
            bin_name = stockout_form.stockout_from
        else:
            stocktemp_form = Former_rack_bin_temp.objects.filter(stock_form=stockform).first()
            if stocktemp_form:
                bin_name = stocktemp_form.from_bin
            else:
                bin_name = 'NONE'

        return JsonResponse({
            "stockform": stockform,
            "bin": bin_name,
            "status": "success"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_rfid_epc_api(request):
    controller_ip = get_controller_ip(get_client_ip(request))
    pid = request.GET.get("pid")
    action = request.GET.get("action")
    selected_machine = request.GET.get("selected_machine", '')
    stock_form = request.GET.get("stock_form")
    origin_bin = request.GET.get("stockform_bin")

    selected_bin_code = request.GET.get("bin_code", "")

    # 1) BASE = số bản ghi đã trả cho client, chưa pass
    base = RFID_read_log.objects.filter(
        rfid_reader_ip=controller_ip, pid=pid,
        is_passed=False, is_logged=True
    ).count()

    #print(f"get_rfid_epc_api -> controller_ip -> {controller_ip}")
    # 2) CHỈ TRẢ CÁI CHƯA GỬI (is_logged=False), thứ tự tăng theo pk
    latest_epc = RFID_read_log.objects.filter(
        rfid_reader_ip=controller_ip, pid=pid,
        is_passed=False, is_logged=False
    ).order_by('pk')

    data, epcs_to_update = [], []

    try:
        for index, epc in enumerate(latest_epc):
            values = get_former_master_data(epc.basket_no, pid, selected_machine, origin_bin, selected_bin_code)
            if not values:
                continue

            qty = 0 if selected_bin_code == "X" else values[1]
            bin_value = 'X' if selected_bin_code == "X" else values[3]
            # 3) ĐÁNH SỐ CỘNG DỒN
            data.append({
                'count': base + index + 1,
                'epc_raw': values[0],
                'epc_vendor': values[2],
                'epc_qty': qty,
                'bin': bin_value,
            })

            # Đánh dấu đã gửi, để lần sau không trả lại
            epc.is_logged = True
            epcs_to_update.append(epc)

            # Lưu lịch sử một lần cho mỗi log mới
            RFID_read.objects.create(
                basket_no=values[0],
                rfid_reader_ip=controller_ip,
                pid=pid,
                create_by=request.user
            )

            # --- GIỮ NGUYÊN NHÁNH STOCKIN / STOCKOUT CỦA ANH ---
            if action in ("stockin", "stockout"):
                if action == "stockout":
                    obj = Former_bin_data.objects.only('batch_no').filter(basket_no=values[0]).first()
                    if obj:
                        data[-1]["batch_no"] = [
                            obj.batch_no.batch_no,
                            obj.batch_no.former_aql,
                            obj.batch_no.former_type,
                            obj.batch_no.former_vendor,
                            obj.batch_no.former_used_day,
                            obj.batch_no.former_size,
                            obj.batch_no.former_surface or "-"  # coalesce None -> "-"
                        ]
                    else:
                        data[-1]["batch_no"] = ["-", "-", "-", "-", "-", "-", "-"]

                elif action == "stockin":
                    if stock_form:
                        try:
                            stock_form_name = stock_form.split('(')[0].strip()
                            if selected_machine != 'CLEAN':
                                stock_form_size = stock_form.split('(')[1].split(')')[0].strip()
                                stock_form_obj = Former_stockout_form.objects.filter(
                                    stockout_form=stock_form_name,
                                    former_size=stock_form_size
                                ).first()
                            else:
                                stock_form_obj = Former_stockout_form.objects.filter(
                                    stockout_form=stock_form_name,
                                ).first()
                                # ❗️BẢO VỆ None trước khi dùng .batch_no
                                if stock_form_obj and stock_form_obj.batch_no:
                                    stock_form_size = Former_batch_data.objects.filter(
                                        batch_no=stock_form_obj.batch_no
                                    ).values_list('former_size', flat=True).first()
                                else:
                                    stock_form_size = "-"

                            if stock_form_obj and stock_form_obj.batch_no:
                                try:
                                    batch_obj = Former_batch_data.objects.get(batch_no=stock_form_obj.batch_no)
                                    if selected_machine == 'CLEAN':
                                        new_used_day = stock_form_obj.most_batch_used_day
                                    else:
                                        days_diff = (date.today() - stock_form_obj.stockout_date).days
                                        new_used_day = stock_form_obj.most_batch_used_day + days_diff + 10

                                    data[-1]["batch_no"] = [
                                        batch_obj.batch_no,
                                        batch_obj.former_aql,
                                        batch_obj.former_type,
                                        batch_obj.former_vendor,
                                        new_used_day,
                                        stock_form_size,
                                        batch_obj.former_surface or "-"  # coalesce
                                    ]

                                except Former_batch_data.DoesNotExist:
                                    data[-1]["batch_no"] = [
                                        f"RETURN_{stock_form_name}",
                                        1.0, "RETURN",
                                        stock_form_obj.stockout_from or "UNKNOWN",
                                        stock_form_obj.most_batch_used_day,
                                        stock_form_size,
                                        '-'
                                    ]
                            else:
                                data[-1]["batch_no"] = ["-", "-", "NO_FORM", "-", "-", stock_form_size, "-"]

                        except Exception as e:
                            print(f"Error parsing stock_form: {e}")
                            data[-1]["batch_no"] = ["-", "-", "ERROR", "-", "-", "-", "-"]
                    else:
                        obj = Former_bin_data.objects.only('batch_no').filter(basket_no=values[0]).first()
                        if obj:
                            data[-1]["batch_no"] = [
                                obj.batch_no.batch_no,
                                obj.batch_no.former_aql,
                                obj.batch_no.former_type,
                                obj.batch_no.former_vendor,
                                obj.batch_no.former_used_day,
                                obj.batch_no.former_size,
                                obj.batch_no.former_surface or "-",  # coalesce
                            ]
                        else:
                            data[-1]["batch_no"] = ["-", "-", "NEW", "-", "-", "-", "-"]

        if epcs_to_update:
            RFID_read_log.objects.bulk_update(epcs_to_update, ['is_logged'])

    except Exception as e:
        print(e)

    return JsonResponse({'epcs': data})

@require_GET
def get_rfid_epc_data_api(request):
    epcs = request.GET.getlist("epcs[]")
    pid = int(request.GET.get("pid", 1))
    controller_ip = get_controller_ip(get_client_ip(request))
    action_name = request.GET.get("action_name", "")

    results = []

    for epc in epcs:
        try:
            print(epc)
            values = get_former_master_data(epc, pid)
            if not values:
                continue

            RFID_read.objects.create(
                epc=values[1],
                controller_ip=RFID_setting.objects.get(rfid_controller_ip=controller_ip),
                pid=pid,
                create_by=request.user
            )

            result_item = {
                "basket_no": epc,
                "values": values,
                "action_name": action_name
            }

            if action_name == "stockin":
                obj = Former_bin_data.objects.only('former_batch').filter(basket_no=values[1]).first()
                if obj:
                    result_item["batch_no"] = [
                        obj.former_batch.batch_no,
                        obj.former_batch.aql,
                        obj.former_batch.former_type,
                        obj.former_batch.vendor_name
                    ]
                else:
                    result_item["no_batch"] = values[1]

            results.append(result_item)

        except Exception as e:
            print(f"[ERROR] EPC {epc}: {e}")

    return JsonResponse({"results": results})

@csrf_exempt
@require_POST
def set_epc_is_passed(request):
    try:
        data = json.loads(request.body.decode())
        pid = data.get('pid')
        controller_ip = get_controller_ip(data.get('client_ip'))

        if not controller_ip:
            return JsonResponse({'status': 'error', 'message': 'Controller IP not found'}, status=404)

        RFID_read_log.objects.filter(
            controller_ip=controller_ip,
            is_passed=False
        ).update(is_passed=True)

        RFID_read.objects.filter(
            controller_ip=controller_ip,
            is_passed=False
        ).update(is_passed=True)

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
