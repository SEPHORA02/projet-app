from django.urls import path
from frontend import views

urlpatterns = [
    path('api/heartbeat/', views.get_heartbeat, name='heartbeat_api'),
    path('heartbeat/', views.get_heartbeat, name='heartbeat_api'),
]