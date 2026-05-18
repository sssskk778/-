"""
Точка входа для Celery воркера.
"""
from app import create_app
from app.extensions import celery
import app.tasks

app = create_app()