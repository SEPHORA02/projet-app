# # frontend/firebase.py
# import firebase_admin
# from firebase_admin import credentials
# import os

# # Initialize Firebase only if credentials file exists
# firebase_key_path = "config/firebase_key.json"
# FIREBASE_INITIALIZED = False

# if os.path.exists(firebase_key_path):
#     try:
#         cred = credentials.Certificate(firebase_key_path)
#         if not firebase_admin._apps:
#             firebase_admin.initialize_app(cred)
#         FIREBASE_INITIALIZED = True
#     except Exception as e:
#         print(f"Warning: Failed to initialize Firebase: {e}")
# else:
#     print(f"Warning: Firebase credentials not found at {firebase_key_path}")

# frontend/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Variable pour vérifier si Firebase est initialisé
FIREBASE_INITIALIZED = False

# Chemin vers le fichier de credentials
BASE_DIR = Path(__file__).resolve().parent.parent
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

# Si le chemin est relatif, le rendre absolu
if cred_path and not os.path.isabs(cred_path):
    cred_path = os.path.join(BASE_DIR, cred_path)
elif not cred_path:
    # Chemin par défaut
    cred_path = os.path.join(BASE_DIR, "config", "serviceAccountKey.json")

# Initialiser Firebase si le fichier existe
if os.path.exists(cred_path):
    try:
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        FIREBASE_INITIALIZED = True
        logger.info(f"Firebase initialisé avec succès depuis {cred_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de Firebase: {e}")
        FIREBASE_INITIALIZED = False
else:
    logger.warning(f"Fichier de credentials Firebase non trouvé: {cred_path}")
    FIREBASE_INITIALIZED = False

# Client Firestore (uniquement si Firebase est initialisé)
db = firestore.client() if FIREBASE_INITIALIZED else None

def get_firestore_client():
    """Retourne le client Firestore ou None si non initialisé"""
    return db

def verify_firebase_token(id_token):
    """Vérifie un token Firebase et retourne les infos utilisateur"""
    if not FIREBASE_INITIALIZED:
        logger.warning("Firebase non initialisé, impossible de vérifier le token")
        return None
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"Erreur de vérification du token Firebase: {e}")
        return None

def get_user_by_email(email):
    """Récupère un utilisateur Firebase par son email"""
    if not FIREBASE_INITIALIZED:
        return None
    
    try:
        user = auth.get_user_by_email(email)
        return user
    except Exception as e:
        logger.error(f"Erreur récupération utilisateur {email}: {e}")
        return None

def create_patient_document(patient_id, user_data):
    """Crée un document patient dans Firestore"""
    if not FIREBASE_INITIALIZED or not db:
        return None
    
    try:
        doc_ref = db.collection("patients").document(patient_id)
        doc_ref.set({
            "user_id": patient_id,
            "email": user_data.get("email", ""),
            "username": user_data.get("username", ""),
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_active": firestore.SERVER_TIMESTAMP,
            "profile": {
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "age": user_data.get("age", 0),
                "location": user_data.get("location", ""),
                "phone": user_data.get("phone", "")
            }
        })
        return doc_ref
    except Exception as e:
        logger.error(f"Erreur création document patient: {e}")
        return None