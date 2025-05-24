"""stream URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.contrib import admin
from django.urls import path

from stream import consumers
from webcam.views import index, video_feed, get_traffic_light_control_response, post_traffic_light_control_status

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', index),
    path('video_feed/', video_feed, name="video-feed-1"),
    path('traffic_light/get', get_traffic_light_control_response, name="get_traffic_light_control_response"),
    path('traffic_light/post', post_traffic_light_control_status, name="post_traffic_light_control_status"),
    path('ws/pi_comms', consumers.PiConsumer.as_asgi(), name="ws-pi-comms"),
]
