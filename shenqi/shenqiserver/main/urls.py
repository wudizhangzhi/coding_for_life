from main.views import status, sysconf, genid
from django.conf.urls import url, include

urlpatterns = [
    url('xtools/x008/status', status, name='status'),
    url('xtools/x008/sysconf', sysconf, name='sysconf'),
    url('xtools/x008/genid', genid, name='genid'),
]
