"""Services de communication avec l'API FastAPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from django.conf import settings


class ErreurRecuperationDonnees(Exception):
    """Exception levée quand l'API externe ne répond pas."""


@dataclass
class ReponseFastAPI:
    """Structure de données pour documenter les valeurs récupérées."""

    donnees: Dict[str, Any]


def recuperer_donnees_fastapi(patient) -> Dict[str, Any]:
    """Récupère les mesures du patient auprès du backend FastAPI.

    L'URL de base provient de la variable FASTAPI_BASE_URL définie
    dans les settings Django. En cas d'erreur, une exception claire est levée.
    """

    base_url = getattr(settings, "FASTAPI_BASE_URL", None)
    if not base_url:
        raise ErreurRecuperationDonnees(
            "FASTAPI_BASE_URL n'est pas configurée. Ajoutez-la dans vos variables d'environnement."
        )

    endpoint = f"{base_url.rstrip('/')}/patients/{patient.id}/mesures"
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ErreurRecuperationDonnees(
            "Impossible de se connecter au service de données externes."
        ) from exc

    donnees = response.json()
    if not isinstance(donnees, dict):
        raise ErreurRecuperationDonnees("Réponse inattendue reçue depuis l'API FastAPI.")

    return donnees


def analyser_risque_asthme(donnees: Dict[str, Any]) -> Dict[str, Any]:
    """Analyse heuristique pour détecter un risque potentiel de crise d'asthme."""

    def _get_value(keys: List[str], default=None):
        for key in keys:
            if key in donnees:
                return donnees[key]
        return default

    score = 0
    facteurs = []

    heart_rate = _get_value(['heart_rate', 'frequence_cardiaque'])
    if heart_rate and heart_rate > 110:
        score += 1
        facteurs.append(f"Rythme cardiaque élevé ({heart_rate} bpm)")

    spo2 = _get_value(['spo2', 'oxygen_saturation'])
    if spo2 and spo2 < 94:
        score += 2
        facteurs.append(f"Saturation O₂ basse ({spo2}%)")

    pm25 = _get_value(['pm25', 'particules'])
    if pm25 and pm25 > 35:
        score += 1
        facteurs.append(f"Particules PM2.5 élevées ({pm25} µg/m³)")

    aqi = _get_value(['air_quality_index', 'aqi'])
    if aqi and aqi > 100:
        score += 1
        facteurs.append(f"Indice de qualité de l'air dégradé ({aqi})")

    co2 = _get_value(['co2_level', 'co2'])
    if co2 and co2 > 1200:
        score += 1
        facteurs.append(f"Niveau de CO₂ préoccupant ({co2} ppm)")

    risque = score >= 3

    return {
        "risque": risque,
        "score": score,
        "facteurs": facteurs,
        "resume": "Risque potentiel détecté" if risque else "Paramètres sous contrôle",
    }

