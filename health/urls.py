from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('simple-profile/', views.simple_profile, name='simple_profile'),
    path('register/', views.register, name='register'),
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('environment/', views.environment_view, name='environment'),
]

