from wh_former.models import Parameter_data
from wh_former.forms import ManageVendorDataForm
from datetime import datetime

def get_params_form(group, belong):
    form = ManageVendorDataForm(group=group)
    if belong:
        queryset = Parameter_data.objects.filter(group=group, belong__contains=belong).values('code', 'name', 'is_active').order_by('code', 'name')
    else:
        queryset = Parameter_data.objects.filter(group=group).values('code', 'name', 'is_active').order_by('code', 'name')

    return form, queryset


def insert_params_form(request, group, belong):
    form = ManageVendorDataForm(request.POST, group=group)
    if form.is_valid():
        param = form.save(commit=False)
        param.belong = belong
        param.code = f'{group}_{belong}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        if not param.pk:
            param.create_by = request.user
        param.update_by = request.user
        param.save()
    else:
        print(form.errors)
    return form

