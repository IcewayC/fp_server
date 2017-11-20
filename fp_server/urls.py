"""fp_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from webfp import displayWebFP, displayWebFPHistory, getWebFPHistory, uploadNewWebFP

from androidfp import getHistory, uploadNewFP, getJarStatus

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'android.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^fp_getstatus$', getJarStatus),
    url(r'^fp_gethistory$', getHistory),
    url(r'^fp_uploadfp$', uploadNewFP),
    url(r'^webfp/index$', displayWebFP),
    url(r'^webfp/history$', displayWebFPHistory),
    url(r'^webfp/uploadfp$', uploadNewWebFP),
    url(r'^webfp/gethistory$', getWebFPHistory),
    # url(r'^resources/(?P<path>.*)', 'django.views.static.serve', {'document_root':'/var/www/android/resources'}),
] + static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)