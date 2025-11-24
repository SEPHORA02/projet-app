from django.urls import path

from . import views

app_name = 'health'

urlpatterns = [
    path('', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('compte/', views.modifier_compte, name='modifier_compte'),
    path('mot-de-passe/', views.modifier_mot_de_passe, name='modifier_mot_de_passe'),
]

