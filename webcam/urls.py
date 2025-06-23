from django.urls import path
from webcam import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
#? --- AUTHENTICATION URLS ---
    path('auth/register/', views.RegisterView.as_view(), name='auth_register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/<str:username>', views.CurrentUserView.as_view(), name='auth_me'),
#? --- STREAM WEB VIEW URLS ---
    path('index/', views.index),
    path('video_feed/', views.video_feed, name="video-feed-1"),
#? --- REST API URLS ---
    path('traffic_light/get/get_statistics/<str:intersection_id>', views.get_statistics, name="get_statistics"),
    path('traffic_light/post/post_reset_intersection_statistics/<str:intersection_id>', views.post_reset_intersection_statistics, name="post_reset_intersection_statistics"),
    path('traffic_light/get/get_current_intersection_status/<str:intersection_id>', views.get_current_intersection_status, name="get_current_intersection_status"),
    path('traffic_light/post/post_traffic_light_toggle', views.post_traffic_light_toggle, name="post_traffic_light_toggle"),
    path('traffic_light/post/post_traffic_light_all_red', views.post_traffic_light_all_red, name="post_traffic_light_all_red"),
    path('traffic_light/post/post_traffic_light_hazard_mode', views.post_traffic_light_hazard_mode, name="post_traffic_light_hazard_mode"),
    path('traffic_light/post/post_traffic_lights_off', views.post_traffic_lights_off, name="post_traffic_lights_off"),
    path('traffic_light/post/post_traffic_light_resume', views.post_traffic_light_resume, name="post_traffic_light_resume"),
    path('traffic_light/post/post_traffic_light_toggle_smart_algorithm/<str:intersection_id>', views.post_traffic_light_toggle_smart_algorithm, name="post_traffic_light_toggle_smart_algorithm"),
    path('intersection/post/create_intersection', views.create_intersection, name="create_intersection"),
    path('intersection/put/update_intersection/<str:intersection_id>', views.update_intersection, name="update_intersection"),
    path('intersection/get/get_intersection/<str:intersection_id>', views.get_intersection, name="get_intersection"),
    path('intersection/get/get_all_intersections', views.get_all_intersections, name="get_all_intersections"),
    path('intersection/delete/delete_intersection/<str:intersection_id>', views.delete_intersection, name="delete_intersection"),

]