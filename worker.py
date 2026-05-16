"""
Точка входа для Celery воркера.
Файл: worker.py (в корне проекта рядом с run.py)

Запуск:
    celery -A worker.celery worker --loglevel=info
"""
from app import create_app
from app.extensions import celery
import app.tasks  # noqa: F401 — регистрирует задачи

app = create_app()