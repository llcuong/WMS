from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from wh_packing.forms import BinValueForm
from wh_packing.models import Bin_Value
from .forms import WarehouseForm, AreaForm, BinForm
from .models import Warehouse, Area, Bin


# Warehouse
@login_required
def warehouse_create(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST, request.FILES)  # Xử lý dữ liệu POST và FILES
        if form.is_valid():
            # Lưu đối tượng với user hiện tại
            warehouse = form.save(commit=False)  # Không lưu ngay lập tức

            # Gán người dùng vào các trường create_by và update_by
            warehouse.create_by = request.user
            warehouse.update_by = request.user

            # Lưu đối tượng với các trường đã được gán
            warehouse.save()  # Lưu đối tượng vào cơ sở dữ liệu
            return redirect('warehouse_list')  # Điều hướng đến trang thành công
    else:
        form = WarehouseForm()  # Tạo form trống

    return render(request, 'warehouse/warehouse_create.html', locals())


@login_required
def warehouse_list(request):
    # Lấy toàn bộ danh sách warehouse từ cơ sở dữ liệu
    warehouses = Warehouse.objects.all()

    return render(request, 'warehouse/warehouse_list.html', locals())


@login_required
def warehouse_edit(request, warehouse_code):
    warehouse = get_object_or_404(Warehouse, wh_code=warehouse_code)

    if request.method == 'POST':
        form = WarehouseForm(request.POST, request.FILES, instance=warehouse)

        if form.is_valid():
            form.save()  # Lưu các thay đổi vào cơ sở dữ liệu
            return redirect('warehouse_list')  # Điều hướng về danh sách kho
    else:
        form = WarehouseForm(instance=warehouse)

    return render(request, 'warehouse/warehouse_edit.html', locals())


def warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        warehouse.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # AJAX
            return JsonResponse({'message': 'Warehouse deleted successfully.', 'success': True}, status=200)

        return redirect('warehouse_list')

    return JsonResponse({'message': 'Invalid request method.'}, status=400)


def test(request):

    return render(request, 'warehouse/test.html', locals())


def warehouse_show(request, pk):
    if request.method == 'POST':
        form = BinValueForm(request.POST)
        if form.is_valid():
            form.save()
            list_value = list(Bin_Value.objects.values())
            return JsonResponse(list_value, safe=False)

    warehouse = Warehouse.objects.get(wh_code=pk)
    bins = Bin.objects.filter(area__warehouse=warehouse)
    form = BinValueForm()

    bins_status = []

    for bin in bins:
        bin_value_exists = Bin_Value.objects.filter(bin=bin).exists()

        status = 'red' if bin_value_exists else 'green'

        bins_status.append({
            'bin_id': bin.bin_id,
            'status': status,  # Sử dụng biến status đã gán
        })
    return render(request, 'warehouse/test.html', locals())


# Area
@login_required
def area_create(request, wh_code):
    if request.method == 'POST':
        form = AreaForm(request.POST)  # Xử lý dữ liệu POST và FILES
        if form.is_valid():

            area = form.save(commit=False)  # Không lưu ngay lập tức
            # Gán người dùng vào các trường create_by và update_by
            area.create_by = request.user
            area.update_by = request.user

            # Lưu đối tượng với các trường đã được gán
            area.save()  # Lưu đối tượng vào cơ sở dữ liệu
            return redirect('area_by_warehouse', wh_code=wh_code)  # Điều hướng đến trang thành công
    else:
        form = AreaForm(initial={'warehouse': wh_code})  # Tạo form trống

    return render(request, 'warehouse/area_create.html', locals())


def area_list(request):
    areas = Area.objects.all()
    return render(request, 'warehouse/area_list.html', locals())


@login_required
def area_by_warehouse(request, wh_code):
    # Lấy đối tượng Warehouse tương ứng với wh_code
    warehouse = Warehouse.objects.get(wh_code=wh_code)

    if warehouse:
        # Lấy tất cả các Area có wh_code là mã kho của warehouse
        areas = Area.objects.filter(warehouse=warehouse)
    else:
        areas = []

    return render(request, 'warehouse/area_by_warehouse.html', locals())


@login_required
def area_edit(request, area_code):
    area = get_object_or_404(Area, area_id=area_code)
    wh_code = area.warehouse_id

    if request.method == 'POST':
        # Khởi tạo form với dữ liệu từ request
        form = AreaForm(request.POST, request.FILES, instance=area)

        if form.is_valid():
            form.save()  # Lưu các thay đổi vào cơ sở dữ liệu
            return redirect('area_by_warehouse', wh_code=wh_code)
    else:
        form = AreaForm(instance=area)

    return render(request, 'warehouse/area_edit.html', locals())


def area_delete(request, pk):
    area = get_object_or_404(Area, pk=pk)
    wh = Area.objects.get(area_id=area).warehouse_id
    if request.method == 'POST':
        # Xóa đối tượng
        area.delete()

        # Trả về phản hồi AJAX nếu yêu cầu là AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # AJAX
            return JsonResponse({'message': 'Area deleted successfully.', 'redirect': 'warehouse/list/', 'success': True}, status=200)
        else:
            # Điều hướng thông thường nếu không phải là AJAX
            return redirect(area_by_warehouse, wh_code=wh)

    # Không cần render trang riêng cho việc xóa
    return JsonResponse({'message': 'Invalid request method.'}, status=400)


@login_required
def bin_create(request, area_code):
    # Lấy đối tượng Area từ area_code
    area = get_object_or_404(Area, area_id=area_code)

    if request.method == 'POST':
        form = BinForm(request.POST, request.FILES)
        if form.is_valid():
            # Gắn đối tượng area vào form trước khi lưu
            bin = form.save(commit=False)

            # Gán người dùng vào các trường create_by và update_by
            bin.create_by = request.user if request.user.is_authenticated else 'Unknown'
            bin.update_by = request.user if request.user.is_authenticated else 'Unknown'

            bin.area = area
            bin.save()
            return redirect('bin_by_area', area_code=area_code)  # Điều hướng đến trang bin_by_area
    else:
        # Truyền đối tượng area vào form, không phải chỉ area_code
        form = BinForm(initial={'area': area})

    return render(request, 'warehouse/bin_create.html', locals())


def bin_list(request):
    bins = Bin.objects.all()
    return render(request, 'warehouse/bin_list.html', {'bins': bins})


@login_required
def bin_edit(request, bin_code):
    bin = get_object_or_404(Bin, bin_id=bin_code)
    area_code = bin.area_id

    if request.method == 'POST':
        # Khởi tạo form với dữ liệu từ request
        form = BinForm(request.POST, request.FILES, instance=bin)

        if form.is_valid():
            form.save()  # Lưu các thay đổi vào cơ sở dữ liệu
            return redirect('bin_by_area', area_code=area_code)
    else:
        form = BinForm(instance=bin)

    return render(request, 'warehouse/bin_edit.html', locals())


def bin_delete(request, pk):

    bin = get_object_or_404(Bin, pk=pk)

    if request.method == 'POST':
        # Xóa đối tượng
        bin.delete()

        # Trả về phản hồi AJAX nếu yêu cầu là AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # AJAX
            return JsonResponse({'message': 'Bin deleted successfully.', 'success': True}, status=200)

        # Điều hướng thông thường nếu không phải là AJAX
        return redirect('bin_by_area', area_code=bin.area.area_id)

    # Không cần render trang riêng cho việc xóa
    return JsonResponse({'message': 'Invalid request method.'}, status=400)


@login_required
def bin_by_area(request, area_code):
    # Lấy đối tượng Warehouse tương ứng với wh_code
    area = Area.objects.get(area_id=area_code)
    wh_code = area.warehouse_id

    if area:
        # Lấy tất cả các Area có wh_code là mã kho của warehouse
        bins = Bin.objects.filter(area=area)
    else:
        bins = []

    # Truyền dữ liệu vào context
    return render(request, 'warehouse/bin_by_area.html', locals())


