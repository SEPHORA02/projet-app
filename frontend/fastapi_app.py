# frontend/fastapi_app.py
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .firebase import (
    get_firestore_client, 
    FIREBASE_INITIALIZED, 
    verify_firebase_token,
    create_patient_document
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Création de l'application FastAPI
app = FastAPI(
    title="E-Santé API avec IA",
    description="API pour recevoir les mesures des patients et analyse IA",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# MODELES DE DONNÉES
# ===============================

class CapteurPayload(BaseModel):
    """Modèle pour les données du capteur ESP8266"""
    humidity: float = Field(..., description="Humidité en %")
    co2_ppm: float = Field(..., description="Niveau de CO2 en ppm")
    spo2: float = Field(..., description="Saturation en oxygène %")
    bpm: float = Field(..., description="Fréquence cardiaque")
    alert: str = Field("normal", description="Niveau d'alerte")

class MesureAvecTimestamp(CapteurPayload):
    """Mesure avec timestamp ajouté"""
    timestamp: str
    patient_id: str

class AnalyseResultat(BaseModel):
    """Résultat de l'analyse IA"""
    resume: str
    risque: bool
    facteurs: List[str]
    recommandations: List[str]
    source: str = "ollama"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# ===============================
# FONCTIONS UTILITAIRES
# ===============================

def _generer_prompt_analyse(mesure: CapteurPayload) -> str:
    """Génère le prompt pour l'IA"""
    return f"""
Tu es un assistant médical spécialisé en asthme. Analyse ces données et réponds UNIQUEMENT en JSON valide avec les clés: resume, risque (true/false), facteurs (liste), recommandations (liste).

Données du patient:
- Fréquence cardiaque: {mesure.bpm} BPM
- Saturation O2: {mesure.spo2}%
- CO2 ambiant: {mesure.co2_ppm} ppm
- Humidité: {mesure.humidity}%
- Alerte actuelle: {mesure.alert}

Seuils critiques:
- SpO2 < 94% → hypoxie
- CO2 > 1200 ppm → air confiné
- BPM > 100 → tachycardie
- Humidité > 70% → risque moisissures

JSON uniquement:
"""

async def _analyser_avec_ollama(prompt: str) -> AnalyseResultat:
    """Appelle Ollama pour analyser les données"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
            )
        response.raise_for_status()
        
        result = response.json()
        contenu = result.get("response", "{}")
        
        # Parser le JSON
        import json
        try:
            data = json.loads(contenu)
        except:
            data = {
                "resume": contenu[:200],
                "risque": False,
                "facteurs": [],
                "recommandations": ["Analyse non structurée"]
            }
        
        return AnalyseResultat(**data)
        
    except Exception as e:
        logger.error(f"Erreur appel Ollama: {e}")
        # Analyse de fallback
        return AnalyseResultat(
            resume="Analyse automatique (IA indisponible)",
            risque=mesure.spo2 < 94 or mesure.co2_ppm > 1200,
            facteurs=[],
            recommandations=["Consultez un médecin en cas de symptômes"]
        )

# ===============================
# ENDPOINTS API
# ===============================

@app.post("/patients/{username}/mesures")
async def recevoir_mesure(
    username: str, 
    mesure: CapteurPayload,
    background_tasks: BackgroundTasks
):
    """
    Reçoit une mesure d'un patient et l'enregistre dans Firestore
    """
    if not FIREBASE_INITIALIZED:
        logger.error("Firebase n'est pas initialisé")
        raise HTTPException(status_code=503, detail="Service Firebase non disponible")
    
    db = get_firestore_client()
    if not db:
        raise HTTPException(status_code=503, detail="Base de données non disponible")
    
    try:
        # Créer la mesure avec timestamp
        now = datetime.now()
        data = mesure.dict()
        data["timestamp"] = now.isoformat()
        data["patient_id"] = username
        
        # Référence Firestore
        doc_ref = db.collection("patients").document(username).collection("mesures").document()
        doc_ref.set(data)
        
        logger.info(f"Mesure enregistrée pour {username}: BPM={mesure.bpm}, SpO2={mesure.spo2}")
        
        # Analyser en arrière-plan
        background_tasks.add_task(analyser_et_alerter, username, mesure)
        
        return {
            "status": "ok", 
            "message": "Mesure enregistrée",
            "timestamp": now.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/patients/{patient_id}/samples-ia")
async def soumettre_mesures_avec_ia(
    patient_id: str,
    payload: CapteurPayload,
    user=Depends(verify_firebase_token)
):
    """
    Endpoint sécurisé avec analyse IA (pour l'application mobile/web)
    """
    if not user or user["uid"] != patient_id:
        raise HTTPException(status_code=403, detail="Accès interdit")
    
    if not FIREBASE_INITIALIZED:
        raise HTTPException(status_code=503, detail="Service Firebase non disponible")
    
    db = get_firestore_client()
    
    try:
        # Analyser avec Ollama
        prompt = _generer_prompt_analyse(payload)
        resultat = await _analyser_avec_ollama(prompt)
        
        # Stocker dans Firestore
        doc_ref = db.collection("patients").document(patient_id)
        sample_ref = doc_ref.collection("samples").document()
        sample_ref.set({
            "payload": payload.dict(),
            "analyse": resultat.dict(),
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        # Créer une alerte si risque détecté
        if resultat.risque:
            alert_ref = doc_ref.collection("alertes").document()
            alert_ref.set({
                "type": "warning",
                "message": resultat.resume,
                "facteurs": resultat.facteurs,
                "recommandations": resultat.recommandations,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "lu": False
            })
        
        return resultat
        
    except Exception as e:
        logger.error(f"Erreur analyse IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_id}/mesures")
async def recuperer_mesures(
    patient_id: str,
    limit: int = 10,
    user=Depends(verify_firebase_token)
):
    """Récupère les dernières mesures d'un patient"""
    
    if not user or user["uid"] != patient_id:
        raise HTTPException(status_code=403, detail="Accès interdit")
    
    if not FIREBASE_INITIALIZED:
        raise HTTPException(status_code=503, detail="Service Firebase non disponible")
    
    db = get_firestore_client()
    
    try:
        docs = (
            db.collection("patients")
            .document(patient_id)
            .collection("mesures")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        
        resultats = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            resultats.append(data)
        
        if not resultats:
            raise HTTPException(status_code=404, detail="Aucune donnée trouvée")
        
        return resultats
        
    except Exception as e:
        logger.error(f"Erreur récupération mesures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Vérifie l'état de l'API"""
    return {
        "status": "healthy",
        "firebase_initialized": FIREBASE_INITIALIZED,
        "timestamp": datetime.now().isoformat()
    }

# ===============================
# TÂCHES ARRIÈRE-PLAN
# ===============================

async def analyser_et_alerter(username: str, mesure: CapteurPayload):
    """Analyse les données et crée des alertes si nécessaire"""
    
    if not FIREBASE_INITIALIZED:
        return
    
    db = get_firestore_client()
    
    # Logique d'alerte simple
    alertes = []
    
    if mesure.spo2 < 94:
        alertes.append({
            "type": "critique",
            "message": f"Saturation O2 basse: {mesure.spo2}%",
            "valeur": mesure.spo2,
            "seuil": 94
        })
    
    if mesure.co2_ppm > 1200:
        alertes.append({
            "type": "warning",
            "message": f"CO2 élevé: {mesure.co2_ppm} ppm",
            "valeur": mesure.co2_ppm,
            "seuil": 1200
        })
    
    if mesure.bpm > 100:
        alertes.append({
            "type": "info",
            "message": f"Fréquence cardiaque élevée: {mesure.bpm} BPM",
            "valeur": mesure.bpm,
            "seuil": 100
        })
    
    # Enregistrer les alertes
    for alerte in alertes:
        alert_ref = db.collection("patients").document(username).collection("alertes").document()
        alert_ref.set({
            **alerte,
            "timestamp": datetime.now().isoformat(),
            "lu": False
        })
        logger.info(f"Alerte créée pour {username}: {alerte['message']}")