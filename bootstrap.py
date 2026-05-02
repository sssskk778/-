# bootstrap.py
import os
from app import create_app, db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print('✅ Таблицы пересозданы')
    from app.seed import seed_everything
    seed_everything()