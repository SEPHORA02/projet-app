# import os
# from typing import Dict, Optional

# import httpx
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field


# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# app = FastAPI(
#     title="Service IA Asthme",
#     description="Expose une API FastAPI qui délègue l'analyse à Ollama.",
#     version="0.1.0",
# )


# class CapteurPayload(BaseModel):
#     heart_rate: int = Field(..., description="Battements par minute")
#     spo2: float = Field(..., description="Saturation O₂ en %")
#     pm25: float = Field(..., description="Particules fines en µg/m³")
#     aqi: int = Field(..., description="Indice global de qualité de l'air")
#     co2: int = Field(..., description="Teneur en CO₂ (ppm)")
#     temperature: Optional[float] = Field(
#         default=None, description="Température corporelle si disponible"
#     )
#     location: Optional[str] = Field(
#         default=None, description="Ville / position du patient"
#     )


# class AnalyseResultat(BaseModel):
#     resume: str
#     risque: bool
#     facteurs: list[str]
#     recommandations: list[str]
#     source: str = "ollama"


# # Stockage naïf des derniers relevés (dev/prototypage).
# MESURES: Dict[str, Dict[str, any]] = {}


# def _prompt_from_payload(patient_id: str, payload: CapteurPayload) -> str:
#     return (
#         "Tu es un assistant médical spécialisé en asthme.\n"
#         "Analyse les données suivantes et réponds en JSON strict avec les clés "
#         "`resume`, `risque` (true/false), `facteurs` (liste de phrases courtes) et "
#         "`recommandations` (liste de suggestions actionnables).\n\n"
#         f"Patient: {patient_id}\n"
#         f"Battements par minute: {payload.heart_rate}\n"
#         f"Saturation O2: {payload.spo2}\n"
#         f"PM2.5: {payload.pm25}\n"
#         f"Indice AQI: {payload.aqi}\n"
#         f"CO2: {payload.co2}\n"
#         f"Température: {payload.temperature}\n"
#         f"Localisation: {payload.location}\n"
#         "Considère les seuils suivants: SpO2 < 94, PM2.5 > 35, AQI > 100, "
#         "CO2 > 1200, fréquence cardiaque > 110.\n"
#         "Explique clairement si une crise d'asthme est probable.\n"
#     )


# async def analyser_avec_ollama(prompt: str) -> AnalyseResultat:
#     async with httpx.AsyncClient(timeout=30) as client:
#         response = await client.post(
#             f"{OLLAMA_BASE_URL}/api/generate",
#             json={
#                 "model": OLLAMA_MODEL,
#                 "prompt": prompt,
#                 "stream": False,
#             },
#         )
#     response.raise_for_status()

#     try:
#         contenu = response.json().get("response", "")
#         data = httpx.Response(200, text=contenu).json()
#     except Exception:
#         data = {
#             "resume": contenu.strip() or "Analyse indisponible",
#             "risque": False,
#             "facteurs": [],
#             "recommandations": [],
#         }

#     return AnalyseResultat(**data)


# @app.post(
#     "/patients/{patient_id}/samples",
#     response_model=AnalyseResultat,
#     summary="Soumettre de nouvelles mesures capteurs et lancer l'analyse IA.",
# )
# async def soumettre_mesures(patient_id: str, payload: CapteurPayload):
#     prompt = _prompt_from_payload(patient_id, payload)
#     resultat = await analyser_avec_ollama(prompt)

#     MESURES[patient_id] = {
#         "payload": payload.dict(),
#         "analyse": resultat.dict(),
#     }

#     return resultat


# @app.get(
#     "/patients/{patient_id}/mesures",
#     summary="Récupérer la dernière mesure + analyse effectuée",
# )
# async def recuperer_mesures(patient_id: str):
#     data = MESURES.get(patient_id)
#     if not data:
#         raise HTTPException(status_code=404, detail="Aucune donnée pour ce patient.")
#     return data


# @app.get("/", include_in_schema=False)
# async def racine():
#     return {
#         "message": "Service IA Asthme via FastAPI + Ollama",
#         "routes": [
#             "POST /patients/{patient_id}/samples",
#             "GET /patients/{patient_id}/mesures",
#         ],
#     }


import os
from typing import Dict, Optional

import httpx
import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field


# ===============================
# INITIALISATION FIREBASE
# ===============================

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ===============================
# CONFIG OLLAMA
# ===============================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


app = FastAPI(
    title="Service IA Asthme sécurisé",
    version="2.0.0",
)


# ===============================
# MODELES
# ===============================

class CapteurPayload(BaseModel):
    heart_rate: int
    spo2: float
    pm25: float
    aqi: int
    co2: int
    temperature: Optional[float] = None
    location: Optional[str] = None


class AnalyseResultat(BaseModel):
    resume: str
    risque: bool
    facteurs: list[str]
    recommandations: list[str]
    source: str = "ollama"


# ===============================
# SECURITE FIREBASE JWT
# ===============================

async def verifier_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token invalide")

    token = authorization.split(" ")[1]

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Token Firebase invalide")


# ===============================
# PROMPT IA
# ===============================

def _prompt_from_payload(payload: CapteurPayload) -> str:
    return f"""
Tu es un assistant médical spécialisé en asthme.
Réponds uniquement en JSON strict avec les clés:
resume, risque (true/false), facteurs, recommandations.

Données:
- BPM: {payload.heart_rate}
- SpO2: {payload.spo2}
- PM2.5: {payload.pm25}
- AQI: {payload.aqi}
- CO2: {payload.co2}
- Température: {payload.temperature}
- Localisation: {payload.location}

Seuils critiques:
SpO2 < 94
PM2.5 > 35
AQI > 100
CO2 > 1200
BPM > 110
"""


# ===============================
# ANALYSE IA
# ===============================

async def analyser_avec_ollama(prompt: str) -> AnalyseResultat:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )

    response.raise_for_status()
    contenu = response.json().get("response", "")

    try:
        data = httpx.Response(200, text=contenu).json()
    except Exception:
        data = {
            "resume": contenu.strip(),
            "risque": False,
            "facteurs": [],
            "recommandations": [],
        }

    return AnalyseResultat(**data)


# ===============================
# ENDPOINTS SECURISES
# ===============================

@app.post("/patients/{patient_id}/samples", response_model=AnalyseResultat)
async def soumettre_mesures(
    patient_id: str,
    payload: CapteurPayload,
    user=Depends(verifier_token)
):
    if user["uid"] != patient_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    prompt = _prompt_from_payload(payload)
    resultat = await analyser_avec_ollama(prompt)

    # Stockage Firestore
    doc_ref = db.collection("patients").document(patient_id)
    doc_ref.collection("samples").add({
        "payload": payload.dict(),
        "analyse": resultat.dict(),
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    return resultat


@app.get("/patients/{patient_id}/mesures")
async def recuperer_mesures(
    patient_id: str,
    user=Depends(verifier_token)
):
    if user["uid"] != patient_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    docs = (
        db.collection("patients")
        .document(patient_id)
        .collection("samples")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    result = list(docs)
    if not result:
        raise HTTPException(status_code=404, detail="Aucune donnée")

    return result[0].to_dict()
