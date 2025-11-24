"""Services de communication avec l'API FastAPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

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

