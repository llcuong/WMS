import socket
import datetime
from django.utils.translation import gettext as _
from django.http import Http404
from django.urls import reverse
from users.models import CustomUser



def get_datetime_str():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d%H%M%S")


def get_date_str():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d")


def get_form_json(form):
    json = ''
    for field in form.fields:
        json += "{field:'"+ field +"', title: '"+ form[field].label +"'},"
    json += "{'field': 'pk', 'title': '鍵值', 'visible': 'false'}"
    json = "["+json+"]"
    return json


def get_home_url(request):
    obj = CustomUser.objects.get(pk=request.user.pk)
    pk = obj.setting_user.first().default.pk

    if pk:
        return reverse('project_manage', kwargs={'pk': pk})
    else:
        return reverse('login')


def get_status_dropdown(o_request):
    tmp = ""
    status_html = """<div class="btn-group dropdown">
                      <button class="btn btn-info dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        {title}
                      </button>
                      <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                        {tmp}
                      </div>
                    </div>
                    <input type="hidden" name="request_id" id="request_id" value={request_id} \>
                    <input type="hidden" name="status_id" id="status_id" \>
                    """

    status = Status.objects.all()
    for s in status:
        active = ""
        if s == o_request.status:
            active = "active"
        tmp += "<a class=\"dropdown-item {active}\" href=\"#\" onclick=\"change_status('{status_value}');\">{status_name}</a>"
        tmp = tmp.format(active=active, status_value=s.id, status_name=s.status_en)

    status_html = status_html.format(title=_("Update Status"), tmp=tmp, request_id=o_request.id)
    return status_html


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def get_batch_no():
    now = datetime.datetime.now()
    batch_no = now.strftime("%y%m%d%H%M%S")
    return batch_no
