from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('connexion/', views.login_view, name='connexion'),
    path('inscription/', views.register_view, name='inscription'),
    path('deconnexion/', views.logout_view, name='deconnexion'),

    # Dashboard & pages
    path('tableau-bord/', views.dashboard_view, name='tableau_bord'),
    path('historique/', views.history_view, name='historique'),          # ← history_view
    path('rapports/', views.report_view, name='rapports'),                # ← report_view
    path('alertes/', views.alerts_view, name='alertes'),                  # ← alerts_view
    path('parametres/', views.settings_view, name='parametres'),         # ← settings_view
]