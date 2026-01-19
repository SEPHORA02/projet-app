"""
Exemple: Comment envoyer les alertes de FastAPI vers Django

Ajouter ce code dans votre API FastAPI (API/main.py)
"""

import httpx
import logging

logger = logging.getLogger("asthma_monitor")

# Configuration Django
DJANGO_URL = "http://localhost:8000"
DJANGO_API_KEY = "your-secure-api-key-here"  # À mettre dans .env


async def send_alert_to_django(alert_payload):
    """
    Envoie une alerte vers Django
    
    Args:
        alert_payload: dict avec la structure de l'alerte
        
    Exemple:
        alert_payload = {
            "patient_id": "patient_123",
            "alert_type": "asthma_risk",
            "severity": "high",
            "message": "Risque d'asthme élevé détecté",
            "sensor_data": {
                "heartRate": 120,
                "respiratoryRate": 28,
                "bodyTemperature": 37.2,
                "co2": 850
            },
            "ai_analysis": {
                "confidence": 0.95,
                "risk_factors": ["tachycardie", "tachypnée"]
            },
            "recommendations": [
                "Utilisez votre inhalateur de secours",
                "Restez au calme",
                "Contactez votre médecin si les symptômes persistent"
            ]
        }
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DJANGO_URL}/api/alerts/receive/",
                json=alert_payload,
                headers={
                    "Authorization": f"Bearer {DJANGO_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ Alerte envoyée à Django (ID: {result.get('alert_id')})")
                return True
            else:
                logger.error(f"✗ Erreur Django: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Impossible d'envoyer l'alerte à Django: {e}")
        return False


# MODIFICATION EXEMPLE DU CODE EXISTANT DE FastAPI:

"""
# Dans votre fonction d'analyse (exemple):

async def analyze_and_alert(sensor_data: SensorData):
    # ... votre logique d'analyse ...
    
    if should_alert:
        # Préparer le payload pour Django
        alert_payload = {
            "patient_id": "default_patient",  # À modifier selon votre logique
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "sensor_data": sensor_data.dict(),
            "ai_analysis": {
                "confidence": confidence,
                "risk_factors": risk_factors,
                "ai_model": "mistral",
                "processing_time": processing_time
            },
            "recommendations": recommendations
        }
        
        # Envoyer à Django
        await send_alert_to_django(alert_payload)
"""


# EXEMPLE COMPLET D'INTÉGRATION:

"""
# À ajouter dans main.py (FastAPI):

@app.post("/alerts/send-to-django")
async def send_alert_to_django_endpoint(alert_data: AlertPayload):
    '''Endpoint pour envoyer manuellement une alerte à Django'''
    success = await send_alert_to_django(alert_data.dict())
    return {
        "status": "success" if success else "error",
        "message": "Alerte envoyée à Django"
    }


# Ou pour envoyer automatiquement:

async def background_alert_sender():
    '''Vérifie les alertes non envoyées et les envoie à Django'''
    while True:
        try:
            # Récupérer les alertes depuis votre stockage
            alerts = get_unsent_alerts()  # Votre implémentation
            
            for alert in alerts:
                await send_alert_to_django(alert)
                mark_alert_as_sent(alert.id)
                
            await asyncio.sleep(5)  # Vérifier toutes les 5 secondes
        except Exception as e:
            logger.error(f"Erreur dans background_alert_sender: {e}")
            await asyncio.sleep(5)


# Dans lifespan:

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    task = asyncio.create_task(background_alert_sender())
    yield
    # Fermeture
    task.cancel()
"""
