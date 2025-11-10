from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('environment/', views.environment_view, name='environment'),
]

