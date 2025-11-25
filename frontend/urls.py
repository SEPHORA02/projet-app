from django.urls import path
from .views.auth_views import *
from .views.dashboard_views import *

urlpatterns = [
    # Authentication
    path('connexion/', connexion, name='connexion'),
    path('inscription/', inscription, name='inscription'),
    path('deconnexion/', deconnexion, name='deconnexion'),
    
    # Dashboard
    path('tableau-bord/', tableau_bord, name='tableau_bord'),
    path('historique/', historique, name='historique'),
    path('rapports/', rapports, name='rapports'),
    path('alertes/', alertes, name='alertes'),
    path('parametres/', parametres, name='parametres'),
]