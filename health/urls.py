from django.urls import path
from . import views

urlpatterns = [
    path('api/heartbeat/', views.get_heartbeat, name='heartbeat_api'),
]