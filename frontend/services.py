"""
Service pour intégrer avec l'API FastAPI
"""

import requests
import logging
from django.conf import settings
from .models import Alert

logger = logging.getLogger(__name__)


class FastAPIAlertService:
    """Service pour récupérer et gérer les alertes depuis FastAPI"""
    
    def __init__(self):
        self.fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://localhost:9000')
        self.timeout = 5
    
    def fetch_alerts_from_fastapi(self):
        """Récupère les alertes depuis l'API FastAPI"""
        try:
            response = requests.get(
                f"{self.fastapi_url}/alerts",
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Impossible de récupérer les alertes depuis FastAPI: {e}")
            return []
    
    def save_alert_to_django(self, alert_data):
        """Sauvegarde une alerte dans Django"""
        try:
            # Déterminer le type d'alerte et la sévérité
            alert_type = alert_data.get('alert_type', 'info')
            severity = alert_data.get('severity', 'low')
            
            # Créer ou mettre à jour l'alerte
            alert, created = Alert.objects.update_or_create(
                patient_id=alert_data.get('patient_id', 'default_patient'),
                timestamp=alert_data.get('timestamp', None),
                defaults={
                    'alert_type': alert_type,
                    'severity': severity,
                    'message': alert_data.get('message', ''),
                    'sensor_data': alert_data.get('sensor_data', {}),
                    'ai_analysis': alert_data.get('ai_analysis', {}),
                    'recommendations': alert_data.get('recommendations', []),
                }
            )
            return alert, created
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'alerte: {e}")
            return None, False
    
    def get_recent_alerts(self, limit=50):
        """Retourne les alertes récentes depuis Django"""
        return Alert.objects.filter(is_dismissed=False).order_by('-timestamp')[:limit]
    
    def get_alert_stats(self):
        """Retourne les statistiques des alertes"""
        alerts = Alert.objects.filter(is_dismissed=False)
        return {
            'total': alerts.count(),
            'critical': alerts.filter(severity='critical').count(),
            'high': alerts.filter(severity='high').count(),
            'medium': alerts.filter(severity='medium').count(),
            'low': alerts.filter(severity='low').count(),
            'unread': alerts.filter(is_read=False).count(),
        }


# Instance unique du service
alert_service = FastAPIAlertService()
