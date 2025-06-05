from django.urls import path

from webcam import views

urlpatterns = [
    path('index/', views.index),
    path('video_feed/', views.video_feed, name="video-feed-1"),
    path('traffic_light/get/get_statistics', views.get_statistics, name="get_statistics"),
    path('traffic_light/get/get_current_intersection_status', views.get_current_intersection_status, name="get_current_intersection_status"),
    path('traffic_light/post/post_traffic_light_toggle', views.post_traffic_light_toggle, name="post_traffic_light_toggle"),
    path('traffic_light/post/post_traffic_light_all_red', views.post_traffic_light_all_red, name="post_traffic_light_all_red"),
    path('traffic_light/post/post_traffic_light_hazard_mode', views.post_traffic_light_hazard_mode, name="post_traffic_light_hazard_mode"),
    path('traffic_light/post/post_traffic_lights_off', views.post_traffic_lights_off, name="post_traffic_lights_off"),
    path('traffic_light/post/post_traffic_light_resume', views.post_traffic_light_resume, name="post_traffic_light_resume"),
    path('traffic_light/post/post_traffic_light_toggle_smart_algorithm', views.post_traffic_light_toggle_smart_algorithm, name="post_traffic_light_toggle_smart_algorithm"),
]