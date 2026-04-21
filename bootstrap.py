# bootstrap.py
import os
from sqlalchemy import text
from app import create_app, db

# Удаляем старую БД
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print('🗑️ Старая БД удалена')

app = create_app()
with app.app_context():
    # Применяем миграции
    from flask_migrate import upgrade

    upgrade()

    print('✅ База данных создана')

    # Заполняем данными
    from app.seed import seed_everything

    seed_everything()