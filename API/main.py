"""
Système de surveillance d'asthme avec FastAPI et Mistral AI
Fichier principal contenant toute l'application
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import uvicorn
import httpx
import json
import logging
import sys
import asyncio
from typing import Optional, Dict, Any, Tuple
from datetime import datetime


# ==================== CONFIGURATION ====================

class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # URLs
    SENSOR_API_URL: str = Field(default="http://192.168.1.83/api/sensors")
    MISTRAL_API_URL: str = Field(default="http://localhost:11434/api/generate")
    MISTRAL_MODEL: str = Field(default="mistral")
    DASHBOARD_URL: str = Field(default="http://localhost:8000/alertes/")
    
    # Monitoring
    MONITORING_INTERVAL: int = Field(default=5)
    ERROR_RETRY_INTERVAL: int = Field(default=30)
    
    # Seuils vitaux
    HEART_RATE_MAX: int = Field(default=100)
    HEART_RATE_MIN: int = Field(default=50)
    RESPIRATORY_RATE_MAX: int = Field(default=25)
    RESPIRATORY_RATE_MIN: int = Field(default=12)
    BODY_TEMP_MAX: float = Field(default=38.0)
    BODY_TEMP_MIN: float = Field(default=36.0)
    
    # Seuils environnement
    CO2_MAX: int = Field(default=1000)
    HUMIDITY_MAX: int = Field(default=70)
    HUMIDITY_MIN: int = Field(default=30)
    RISK_LEVEL_THRESHOLD: int = Field(default=50)
    
    # Timeouts
    HTTP_TIMEOUT: int = Field(default=10)
    MISTRAL_TIMEOUT: int = Field(default=60)
    
    # Sécurité
    DJANGO_API_KEY: Optional[str] = Field(default=None)
    DEBUG: bool = Field(default=False)
    
    # Notifications
    SEND_NORMAL_NOTIFICATIONS: bool = Field(
        default=True,
        description="Envoyer des notifications même pour données normales"
    )
    
    # Configuration UI
    CONFIG_PORT: int = Field(default=8080, description="Port pour l'interface de configuration")
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore les champs supplémentaires non définis

settings = Settings()


# ==================== LOGGER ====================

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
logger = logging.getLogger("asthma_monitor")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, "%Y-%m-%d %H:%M:%S"))
logger.addHandler(console_handler)
logger.propagate = False


# ==================== MODÈLES ====================

class SensorData(BaseModel):
    """Données des capteurs"""
    heartRate: int = Field(..., ge=0, le=250)
    bodyTemperature: float = Field(..., ge=30.0, le=45.0)
    respiratoryRate: int = Field(..., ge=0, le=60)
    ambientTemperature: float
    humidity: int = Field(..., ge=0, le=100)
    co2: int = Field(..., ge=0)
    riskLevel: int = Field(..., ge=0, le=100)
    timestamp: int
    
    @validator('heartRate')
    def validate_heart_rate(cls, v):
        if v < 30 or v > 220:
            raise ValueError(f"Fréquence cardiaque anormale: {v} bpm")
        return v


class AlertPayload(BaseModel):
    """Alerte envoyée au dashboard"""
    patient_id: str = Field(default="default_patient")
    alert_type: str = Field(default="asthma_risk")
    severity: str
    message: str
    sensor_data: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    recommendations: list[str] = Field(default_factory=list)


class AlertResponse(BaseModel):
    """Réponse API"""
    alert_sent: bool
    should_alert: bool
    message: str
    analysis: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== DÉTECTEUR D'ANOMALIES ====================

class AnomalyDetector:
    """Détecte les anomalies avant analyse IA"""
    
    def detect_anomaly(self, data: SensorData) -> Tuple[bool, str]:
        anomalies = []
        
        if data.riskLevel >= settings.RISK_LEVEL_THRESHOLD:
            anomalies.append(f"Niveau de risque élevé ({data.riskLevel}/100)")
        
        if data.heartRate > settings.HEART_RATE_MAX:
            anomalies.append(f"Tachycardie ({data.heartRate} bpm)")
        elif data.heartRate < settings.HEART_RATE_MIN:
            anomalies.append(f"Bradycardie ({data.heartRate} bpm)")
        
        if data.respiratoryRate > settings.RESPIRATORY_RATE_MAX:
            anomalies.append(f"Tachypnée ({data.respiratoryRate} resp/min)")
        elif data.respiratoryRate < settings.RESPIRATORY_RATE_MIN:
            anomalies.append(f"Bradypnée ({data.respiratoryRate} resp/min)")
        
        if data.bodyTemperature > settings.BODY_TEMP_MAX:
            anomalies.append(f"Hyperthermie ({data.bodyTemperature}°C)")
        elif data.bodyTemperature < settings.BODY_TEMP_MIN:
            anomalies.append(f"Hypothermie ({data.bodyTemperature}°C)")
        
        if data.co2 > settings.CO2_MAX:
            anomalies.append(f"CO2 élevé ({data.co2} ppm)")
        
        if data.humidity > settings.HUMIDITY_MAX:
            anomalies.append(f"Humidité excessive ({data.humidity}%)")
        elif data.humidity < settings.HUMIDITY_MIN:
            anomalies.append(f"Air trop sec ({data.humidity}%)")
        
        if data.heartRate > 100 and data.respiratoryRate > 25:
            anomalies.append("Combinaison tachycardie + tachypnée (critique)")
        
        if data.respiratoryRate > 30:
            anomalies.append("Détresse respiratoire potentielle")
        
        if anomalies:
            return True, " | ".join(anomalies)
        return False, "Paramètres normaux"


# ==================== SERVICES ====================

class SensorService:
    """Récupération des données capteurs"""
    
    def __init__(self):
        self.consecutive_failures = 0
    
    async def fetch_sensor_data(self) -> Optional[SensorData]:
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                response = await client.get(settings.SENSOR_API_URL)
                response.raise_for_status()
                data = response.json()
                sensor_data = SensorData(**data)
                self.consecutive_failures = 0
                return sensor_data
        except httpx.ConnectError:
            self.consecutive_failures += 1
            logger.error(f"Impossible de se connecter au capteur à {settings.SENSOR_API_URL}")
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"Erreur récupération données: {str(e)}")
        
        if self.consecutive_failures >= 3:
            logger.critical(f"⚠️ {self.consecutive_failures} échecs consécutifs! Vérifiez l'URL dans .env")
        return None
    
    async def test_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(settings.SENSOR_API_URL)
                return response.status_code == 200
        except:
            return False


class MistralService:
    """Analyse IA avec Mistral"""
    
    def _build_prompt(self, data: SensorData, anomaly_reason: str) -> str:
        return f"""Tu es un assistant médical IA spécialisé dans la détection des crises d'asthme.

DONNÉES PATIENT:
- Fréquence cardiaque: {data.heartRate} bpm
- Température corporelle: {data.bodyTemperature}°C
- Fréquence respiratoire: {data.respiratoryRate} resp/min
- Température ambiante: {data.ambientTemperature}°C
- Humidité: {data.humidity}%
- CO2: {data.co2} ppm
- Niveau de risque: {data.riskLevel}/100

ANOMALIE: {anomaly_reason}

CONTEXTE:
- FC normale: 60-100 bpm
- Temp normale: 36.5-37.5°C
- FR normale: 12-20 resp/min
- CO2 acceptable: <1000 ppm

SIGNES CRITIQUES ASTHME:
- Tachycardie + tachypnée
- FR > 30 (détresse)
- Combinaison de paramètres anormaux

Réponds UNIQUEMENT en JSON (sans markdown):
{{
  "should_alert": true/false,
  "severity": "low/medium/high/critical",
  "message": "Message pour le patient",
  "recommendations": ["action1", "action2"],
  "confidence": 0.0-1.0,
  "anomalies_detected": ["anomalie1"]
}}

Sois prudent mais pas alarmiste."""
    
    async def analyze_asthma_risk(self, data: SensorData, anomaly: str) -> Optional[Dict[str, Any]]:
        try:
            prompt = self._build_prompt(data, anomaly)
            logger.info("🤖 Envoi à Mistral pour analyse...")
            
            payload = {
                "model": settings.MISTRAL_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3, "top_p": 0.9}
            }
            
            async with httpx.AsyncClient(timeout=settings.MISTRAL_TIMEOUT) as client:
                response = await client.post(settings.MISTRAL_API_URL, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if "response" in result:
                    analysis = json.loads(result["response"])
                    logger.info(f"✅ Analyse reçue - Alerte: {analysis.get('should_alert')}")
                    return analysis
        except httpx.ConnectError:
            logger.error("Impossible de se connecter à Mistral. Vérifiez qu'Ollama est lancé")
        except Exception as e:
            logger.error(f"Erreur Mistral: {str(e)}")
        
        return self._fallback_analysis(data, anomaly)
    
    def _fallback_analysis(self, data: SensorData, anomaly: str) -> Dict[str, Any]:
        """Analyse de secours sans IA"""
        logger.warning("⚠️ Analyse de secours (sans IA)")
        
        is_critical = (
            data.respiratoryRate > 30 or
            (data.heartRate > 120 and data.respiratoryRate > 25) or
            data.riskLevel > 80
        )
        
        if is_critical:
            return {
                "should_alert": True,
                "severity": "critical",
                "message": "⚠️ ATTENTION: Signes critiques détectés!",
                "recommendations": [
                    "Prendre inhalateur de secours",
                    "S'asseoir et respirer calmement",
                    "Appeler urgences si ça persiste"
                ],
                "confidence": 0.7,
                "anomalies_detected": [anomaly]
            }
        elif data.respiratoryRate > 25 or data.heartRate > 100:
            return {
                "should_alert": True,
                "severity": "high",
                "message": "Paramètres anormaux. Surveillez vos symptômes.",
                "recommendations": [
                    "Prendre traitement préventif",
                    "Éviter efforts physiques"
                ],
                "confidence": 0.6,
                "anomalies_detected": [anomaly]
            }
        else:
            return {
                "should_alert": False,
                "severity": "low",
                "message": "Légère anomalie, pas de risque immédiat.",
                "recommendations": ["Continuer à surveiller"],
                "confidence": 0.5,
                "anomalies_detected": [anomaly]
            }
    
    async def check_health(self) -> str:
        try:
            base_url = settings.MISTRAL_API_URL.replace("/api/generate", "")
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{base_url}/api/tags")
                if response.status_code == 200:
                    return "connected"
        except:
            pass
        return "offline"


class DashboardService:
    """Envoi des alertes au dashboard Django"""
    
    async def send_alert(self, sensor_data: SensorData, ai_analysis: Dict[str, Any]) -> bool:
        try:
            alert_payload = AlertPayload(
                severity=ai_analysis.get("severity", "medium"),
                message=ai_analysis.get("message", "Anomalie détectée"),
                sensor_data=sensor_data.model_dump(),
                ai_analysis=ai_analysis,
                recommendations=ai_analysis.get("recommendations", [])
            )
            
            headers = {"Content-Type": "application/json"}
            if settings.DJANGO_API_KEY:
                headers["Authorization"] = f"Bearer {settings.DJANGO_API_KEY}"
            
            logger.info(f"📤 Envoi alerte au dashboard: {settings.DASHBOARD_URL}")
            
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                response = await client.post(
                    settings.DASHBOARD_URL,
                    json=alert_payload.model_dump(),
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"✅ Alerte envoyée (Status: {response.status_code})")
                return True
        except httpx.ConnectError:
            logger.error(f"❌ Dashboard Django inaccessible à {settings.DASHBOARD_URL}")
        except Exception as e:
            logger.error(f"❌ Erreur envoi alerte: {str(e)}")
        return False
    
    async def test_connection(self) -> bool:
        try:
            base_url = settings.DASHBOARD_URL.rsplit("/api", 1)[0]
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(base_url)
                return response.status_code in [200, 404, 403]
        except:
            return False


# ==================== INSTANCES GLOBALES ====================

sensor_service = SensorService()
mistral_service = MistralService()
dashboard_service = DashboardService()
anomaly_detector = AnomalyDetector()
monitoring_task = None


# ==================== SURVEILLANCE CONTINUE ====================

async def continuous_monitoring():
    """Surveillance en boucle des capteurs"""
    logger.info("🚀 Démarrage surveillance continue...")
    
    while True:
        try:
            sensor_data = await sensor_service.fetch_sensor_data()
            
            if sensor_data:
                logger.info(f"📊 Données reçues - RiskLevel: {sensor_data.riskLevel}, "
                           f"HR: {sensor_data.heartRate}, RR: {sensor_data.respiratoryRate}")
                
                is_anomaly, reason = anomaly_detector.detect_anomaly(sensor_data)
                
                if is_anomaly:
                    # ========== ANOMALIE DÉTECTÉE : Analyse avec IA ==========
                    logger.warning(f"⚠️ ANOMALIE: {reason}")
                    logger.info("🤖 Envoi à Mistral pour analyse approfondie...")
                    
                    analysis = await mistral_service.analyze_asthma_risk(sensor_data, reason)
                    
                    if analysis:
                        logger.info(f"✅ Analyse IA reçue - Sévérité: {analysis.get('severity')}")
                        logger.info(f"📤 Envoi notification avec analyse IA au dashboard")
                        
                        alert_sent = await dashboard_service.send_alert(sensor_data, analysis)
                        
                        if alert_sent:
                            logger.info("✅ Notification avec analyse IA envoyée")
                        else:
                            logger.error("❌ Échec envoi notification")
                    else:
                        # Si Mistral échoue, envoyer quand même une alerte basique
                        logger.warning("⚠️ IA indisponible, envoi notification de base")
                        basic_alert = {
                            "should_alert": True,
                            "severity": "medium",
                            "message": f"Anomalie détectée: {reason}",
                            "recommendations": [
                                "Surveiller vos symptômes", 
                                "Consulter un médecin si ça persiste"
                            ],
                            "confidence": 0.3,
                            "anomalies_detected": [reason]
                        }
                        await dashboard_service.send_alert(sensor_data, basic_alert)
                else:
                    # ========== DONNÉES NORMALES : Notification simple ==========
                    logger.debug("✓ Données normales")
                    
                    # Vérifier si on doit envoyer les notifications normales
                    if settings.SEND_NORMAL_NOTIFICATIONS:
                        logger.debug("📤 Envoi notification de routine")
                        
                        # Créer une notification "tout va bien"
                        normal_notification = {
                            "should_alert": False,
                            "severity": "low",
                            "message": "Paramètres de santé normaux",
                            "recommendations": ["Continuez votre routine habituelle"],
                            "confidence": 1.0,
                            "anomalies_detected": []
                        }
                        
                        # Envoyer au dashboard (sans analyse IA car tout va bien)
                        await dashboard_service.send_alert(sensor_data, normal_notification)
                        logger.debug("✅ Notification de routine envoyée")
                    else:
                        logger.debug("ℹ️ Notifications normales désactivées (SEND_NORMAL_NOTIFICATIONS=false)")
            
            await asyncio.sleep(settings.MONITORING_INTERVAL)
            
        except Exception as e:
            logger.error(f"Erreur monitoring: {str(e)}", exc_info=True)
            await asyncio.sleep(settings.ERROR_RETRY_INTERVAL)


# ==================== APPLICATION FASTAPI ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application"""
    global monitoring_task
    
    logger.info("🚀 Démarrage système de surveillance d'asthme")
    logger.info(f"Capteurs: {settings.SENSOR_API_URL}")
    logger.info(f"Mistral: {settings.MISTRAL_API_URL}")
    
    monitoring_task = asyncio.create_task(continuous_monitoring())
    
    yield
    
    logger.info("🛑 Arrêt du système")
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Asthma Monitoring System",
    description="Surveillance d'asthme avec IA (Mistral)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Vérification de santé"""
    return {
        "status": "running",
        "service": "Asthma Monitoring API",
        "mistral_status": await mistral_service.check_health(),
        "sensor_url": settings.SENSOR_API_URL
    }


@app.get("/health")
async def health_check():
    """Vérification complète du système"""
    return {
        "api": "ok",
        "mistral": await mistral_service.check_health(),
        "sensor_connection": await sensor_service.test_connection(),
        "dashboard": await dashboard_service.test_connection()
    }


@app.get("/sensors/latest")
async def get_latest_sensor_data():
    """Dernières données capteurs"""
    try:
        data = await sensor_service.fetch_sensor_data()
        if data:
            return data.model_dump()
        raise HTTPException(status_code=503, detail="Capteur inaccessible")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AlertResponse)
async def analyze_sensor_data(data: SensorData, background_tasks: BackgroundTasks):
    """Analyse manuelle de données"""
    try:
        is_anomaly, reason = anomaly_detector.detect_anomaly(data)
        
        if not is_anomaly:
            return AlertResponse(
                alert_sent=False,
                should_alert=False,
                message="Données normales",
                analysis={"status": "normal"}
            )
        
        analysis = await mistral_service.analyze_asthma_risk(data, reason)
        should_alert = analysis.get("should_alert", False)
        
        if should_alert:
            background_tasks.add_task(dashboard_service.send_alert, data, analysis)
        
        return AlertResponse(
            alert_sent=should_alert,
            should_alert=should_alert,
            message=analysis.get("message", "Analyse effectuée"),
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"Erreur analyse: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/sensor-url")
async def update_sensor_url(new_url: str):
    """Mise à jour URL capteur"""
    try:
        settings.SENSOR_API_URL = new_url
        logger.info(f"URL capteur mise à jour: {new_url}")
        is_connected = await sensor_service.test_connection()
        return {
            "status": "updated",
            "new_url": new_url,
            "connection_ok": is_connected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)