from django.urls import re_path as url
from bases.views import index

urlpatterns = [
    url(r'^', index, name='index'),
]
