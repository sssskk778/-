"""
Расширения приложения — хранит экземпляры celery и других расширений.
Файл: app/extensions.py
"""
from celery import Celery

# Создаётся без конфигурации — настраивается в create_app()
celery = Celery()