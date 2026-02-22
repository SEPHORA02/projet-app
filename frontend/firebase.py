# frontend/firebase.py
import firebase_admin
from firebase_admin import credentials
import os

# Initialize Firebase only if credentials file exists
firebase_key_path = "config/serviceAccountKey.json"
FIREBASE_INITIALIZED = False

if os.path.exists(firebase_key_path):
    try:
        cred = credentials.Certificate(firebase_key_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        FIREBASE_INITIALIZED = True
    except Exception as e:
        print(f"Warning: Failed to initialize Firebase: {e}")
else:
    print(f"Warning: Firebase credentials not found at {firebase_key_path}")
