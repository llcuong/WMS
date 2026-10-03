"""VNWMS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.urls import re_path as url
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from bases.views import index
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    url('admin/', admin.site.urls),
    url(r'^users/', include('users.urls')),
    url(r'^home', include('bases.urls')),
    url(r'^warehouse/', include('warehouse.urls')),
    url(r'^wh_packing/', include('wh_packing.urls')),
    url(r'^wh_former/', include('wh_former.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    url(r'^$', index, name='index'),
)
