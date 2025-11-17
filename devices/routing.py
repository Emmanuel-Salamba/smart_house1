from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/house/(?P<house_id>[^/]+)/$',
        consumers.MobileAppConsumer.as_asgi()
    ),
    re_path(
        r'ws/microcontroller/(?P<microcontroller_id>[^/]+)/(?P<api_key>[^/]+)/$',
        consumers.MicrocontrollerConsumer.as_asgi()
    ),
]