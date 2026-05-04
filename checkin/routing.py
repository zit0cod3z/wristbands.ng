from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/checkin/(?P<event_pk>[0-9a-f-]+)/$', consumers.CheckInConsumer.as_asgi()),
]
