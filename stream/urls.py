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
from webcam.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', index),
    path('video_feed/', video_feed, name="video-feed-1"),
    path('traffic_light/get/get_statistics', get_statistics, name="get_statistics"),
    path('traffic_light/get/get_current_intersection_status', get_current_intersection_status, name="get_current_intersection_status"),
    path('traffic_light/post/post_traffic_light_toggle', post_traffic_light_toggle, name="post_traffic_light_toggle"),
    path('traffic_light/post/post_traffic_light_all_red', post_traffic_light_all_red, name="post_traffic_light_all_red"),
    path('traffic_light/post/post_traffic_light_hazard_mode', post_traffic_light_hazard_mode, name="post_traffic_light_hazard_mode"),
    path('traffic_light/post/post_traffic_lights_off', post_traffic_lights_off, name="post_traffic_lights_off"),
    path('traffic_light/post/post_traffic_light_resume', post_traffic_light_resume, name="post_traffic_light_resume"),
    path('traffic_light/post/post_traffic_light_toggle_smart_algorithm', post_traffic_light_toggle_smart_algorithm, name="post_traffic_light_toggle_smart_algorithm"),
    path('ws/pi_comms', consumers.PiConsumer.as_asgi(), name="ws-pi-comms"),
]
