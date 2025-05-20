import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

json_path = os.getenv("FIREBASE_CREDENTIALS")
if not json_path:
    raise ValueError("FIREBASE_CREDENTIALS no está definido en .env o está vacío.")

# Convertir la ruta a absoluta o relativa desde el script
json_path = Path(json_path)
if not json_path.is_file():
    raise FileNotFoundError(f"Archivo de credenciales no encontrado en: {json_path}")

# Leer el JSON desde el archivo
with open(json_path, "r", encoding="utf-8") as f:
    firebase_credentials = json.load(f)

# Corregir formato de private_key
firebase_credentials["private_key"] = firebase_credentials["private_key"].replace("\\n", "\n").strip()

storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
if not storage_bucket:
    raise ValueError("FIREBASE_STORAGE_BUCKET no está definido en .env o está vacío.")
storage_bucket = storage_bucket.strip()

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})

bucket = storage.bucket()
