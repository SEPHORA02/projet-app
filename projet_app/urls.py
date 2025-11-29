from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from frontend import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('connexion')),
    path('', include('frontend.urls')),
    path('heartbeat', views.get_heartbeat, name='heartbeat_api'),

    path('health/', include('health.urls')),
]
