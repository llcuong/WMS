from django.urls import re_path as url
from bases.views import index
from warehouse.views import warehouse_show, warehouse_edit, warehouse_create, warehouse_list, warehouse_delete, \
    area_edit, area_create, area_by_warehouse, area_delete, area_list, bin_create, bin_edit, bin_list, bin_delete, \
    bin_by_area

urlpatterns = [
    url(r'^warehouse_show/(?P<pk>\w+)/$', warehouse_show, name='warehouse_show'),
    url(r'^warehouse_edit/(?P<warehouse_code>\w+)/$', warehouse_edit, name='warehouse_edit'),
    url(r'^warehouse_create/$', warehouse_create, name='warehouse_create'),
    url(r'^warehouse_delete/(?P<pk>\w+)/$', warehouse_delete, name='warehouse_delete'),
    url(r'^warehouse_list/$', warehouse_list, name='warehouse_list'),

    url(r'^area_edit/(?P<area_code>[^/]+)/$', area_edit, name='area_edit'),
    url(r'^area_create/(?P<wh_code>[^/]+)/$', area_create, name='area_create'),
    url(r'^area_by_warehouse/(?P<wh_code>\w+)/$', area_by_warehouse, name='area_by_warehouse'),
    url(r'^area_delete/(?P<pk>[^/]+)/$', area_delete, name='area-delete'),
    url(r'^area_list/$', area_list, name='area_list'),

    url(r'^bin_create/(?P<area_code>[^/]+)$', bin_create, name='bin_create'),
    url(r'^bin_edit/(?P<bin_code>[^/]+)/$', bin_edit, name='bin_edit'),
    url(r'^bin_list/$', bin_list, name='bin_list'),
    url(r'^bin_by_area/(?P<area_code>[^/]+)$', bin_by_area, name='bin_by_area'),
    url(r'^bin_delete/(?P<pk>[^/]+)/$', bin_delete, name='bin-delete'),
    url(r'^$', index, name='warehouse_index'),

]




