# myapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/pi_comms$', consumers.PiConsumer.as_asgi()),
]