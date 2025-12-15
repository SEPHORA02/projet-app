# frontend/firebase.py
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("config/firebase_key.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
