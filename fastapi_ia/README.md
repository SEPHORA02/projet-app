# Service FastAPI + Ollama

Ce répertoire contient une API FastAPI autonome qui interroge un modèle Ollama
pour analyser des données de capteurs (asthme) et déterminer un éventuel risque.
La logique reste indépendante du projet Django ; vous pouvez la déployer ou la
tester séparément.

## Installation

```bash
cd fastapi_ia
python -m venv .venv
.venv\Scripts\activate   # ou source .venv/bin/activate sur Linux/Mac
pip install -r requirements.txt
```

Assurez-vous qu’Ollama tourne en local (par défaut sur `http://localhost:11434`)
et qu’un modèle (ex : `llama3`) est disponible. Si besoin :

```bash
ollama pull llama3
```

## Variables d’environnement

- `OLLAMA_BASE_URL` (défaut : `http://localhost:11434`)
- `OLLAMA_MODEL` (défaut : `llama3`)

## Lancer l’API

```bash
uvicorn fastapi_ia.main:app --reload --port 8001
```

Endpoints principaux :

- `POST /patients/{patient_id}/samples` : envoie les mesures du capteur et
  récupère l’analyse IA.
- `GET /patients/{patient_id}/mesures` : retourne la dernière mesure et son
  analyse.

Exemple de requête :

```bash
curl -X POST http://localhost:8001/patients/42/samples \
  -H "Content-Type: application/json" \
  -d '{
        "heart_rate": 118,
        "spo2": 93.5,
        "pm25": 42,
        "aqi": 120,
        "co2": 1500,
        "temperature": 37.4,
        "location": "Abidjan"
      }'
```

La réponse inclut un résumé, un indicateur de risque et des recommandations
générées par Ollama.

