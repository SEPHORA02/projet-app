from django.urls import path, include
from . import views

urlpatterns = [
    # Authentification
    path('connexion/', views.login_view, name='connexion'),
    path('inscription/', views.register_view, name='inscription'),
    path('deconnexion/', views.logout_view, name='deconnexion'),
    
     path('accounts/login/', views.login_view, name='login'),  # Redirection Django par défaut

    # Dashboard & pages
    path('tableau-bord/', views.dashboard_view, name='tableau_bord'),
    path('historique/', views.history_view, name='historique'),
    path('rapports/', views.report_view, name='rapports'),
    path('alertes/', views.alerts_view, name='alertes'),
    path('parametres/', views.settings_view, name='parametres'),
    
    # API endpoints pour les alertes (nouvelles routes avec polling temps réel)
    path('api/alertes/', views.get_alerts_json, name='api_alertes'),
    path('api/alertes/<int:alert_id>/read/', views.mark_alert_as_read, name='api_mark_read'),
    path('api/alertes/<int:alert_id>/dismiss/', views.dismiss_alert, name='api_dismiss_alert'),
    path('api/alertes/clear/', views.clear_all_alerts, name='api_clear_alerts'),
    
    # Génération de rapports PDF
    path('generate-report-pdf/', views.generate_report_pdf, name='generate_report_pdf'),
    
    # Anciennes routes (pour compatibilité)
    path('api/alerts/', views.api_get_alerts, name='api_alerts'),
    path('api/alerts/stats/', views.api_get_alerts_stats, name='api_alerts_stats'),
    path('api/alerts/<int:alert_id>/read/', views.api_mark_alert_as_read, name='api_mark_read_old'),
    path('api/alerts/<int:alert_id>/dismiss/', views.api_dismiss_alert, name='api_dismiss_alert_old'),
    path('api/alerts/receive/', views.api_receive_alert_from_fastapi, name='api_receive_alert'),
    
    # Config ESP8266
    path('api/config/esp8266/', views.get_esp8266_config, name='esp8266_config'),
    
    # Health API
    path('api/', include('health.urls')),
]