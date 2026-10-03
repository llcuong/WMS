from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
import json

from wh_former.models import Parameter_data


@csrf_exempt
@login_required
def enable_param_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        param_code = data.get('code')
        try:
            param = Parameter_data.objects.get(code=param_code)
            param.is_active = True
            param.update_by = request.user
            param.save()
            return JsonResponse({'status': 'success', 'message': f'Disabled #{param_code}'})
        except Parameter_data.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Vendor not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@csrf_exempt
@login_required
def disable_param_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        param_code = data.get('code')
        try:
            param = Parameter_data.objects.get(code=param_code)
            param.is_active = False
            param.update_by = request.user
            param.save()
            return JsonResponse({'status': 'success', 'message': f'Disabled #{param_code}'})
        except Parameter_data.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Vendor not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@csrf_exempt
@login_required
@transaction.atomic
def delete_param_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        param_code = data.get('code')
        try:
            param = Parameter_data.objects.get(code=param_code)
            param.delete()
            return JsonResponse({'status': 'success', 'message': f'Deleted #{param_code}'})
        except Parameter_data.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Parameter not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@csrf_exempt
def edit_param_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code')
        name = data.get('name')
        is_active = data.get('is_active')

        try:
            vendor = Parameter_data.objects.get(code=code)
            vendor.name = name
            vendor.is_active = is_active
            vendor.save()
            return JsonResponse({'message': 'Vendor updated successfully!'})
        except Parameter_data.DoesNotExist:
            return JsonResponse({'message': 'Vendor not found!'}, status=404)
    return JsonResponse({'message': 'Invalid request!'}, status=400)