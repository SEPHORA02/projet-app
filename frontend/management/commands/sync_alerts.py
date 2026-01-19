"""
Commande Django pour synchroniser les alertes depuis l'API FastAPI
Usage: python manage.py sync_alerts
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import logging
from frontend.models import Alert
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronise les alertes depuis l\'API FastAPI vers Django'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Nombre maximum d\'alertes à récupérer'
        )
    
    def handle(self, *args, **options):
        fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://localhost:9000')
        limit = options['limit']
        
        try:
            # Récupérer les alertes depuis FastAPI
            response = requests.get(
                f"{fastapi_url}/alerts",
                timeout=5,
                params={'limit': limit}
            )
            response.raise_for_status()
            alerts = response.json()
            
            if not alerts:
                self.stdout.write(self.style.WARNING('Aucune alerte reçue de FastAPI'))
                return
            
            saved_count = 0
            for alert_data in alerts:
                try:
                    # Créer ou mettre à jour l'alerte
                    alert, created = Alert.objects.update_or_create(
                        patient_id=alert_data.get('patient_id', 'default_patient'),
                        timestamp=datetime.fromisoformat(alert_data.get('timestamp', '')),
                        defaults={
                            'alert_type': alert_data.get('alert_type', 'info'),
                            'severity': alert_data.get('severity', 'low'),
                            'message': alert_data.get('message', ''),
                            'sensor_data': alert_data.get('sensor_data', {}),
                            'ai_analysis': alert_data.get('ai_analysis', {}),
                            'recommendations': alert_data.get('recommendations', []),
                        }
                    )
                    if created:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de l'alerte: {e}")
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ {saved_count} nouvelles alertes sauvegardées')
            )
        
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Impossible de se connecter à FastAPI: {e}')
            )
            logger.error(f"Erreur de connexion FastAPI: {e}")
