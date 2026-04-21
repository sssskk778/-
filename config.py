import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE = BASE_DIR / 'instance'
INSTANCE.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'carrier-rating-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{INSTANCE / "app.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
