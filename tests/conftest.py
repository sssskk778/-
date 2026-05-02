import os
import pytest
from app import create_app, db as _db


@pytest.fixture
def app():
    # Переопределяем URI ДО создания приложения
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        _db.create_all()

        from app.models import User, Criterion

        admin = User(username='admin', full_name='Admin', role='admin')
        admin.set_password('admin123')
        _db.session.add(admin)
        _db.session.commit()

        criteria = [
            ('on_time_rate', 'Своевременность доставки', 'benefit'),
            ('cancellation_rate', 'Доля отменённых рейсов', 'cost'),
            ('no_show_rate', 'Доля неявок на погрузку', 'cost'),
            ('damage_rate', 'Доля повреждений груза', 'cost'),
            ('loss_rate', 'Доля утрат груза', 'cost'),
            ('accident_rate', 'Доля рейсов с ДТП', 'cost'),
            ('tracking_compliance', 'Доля рейсов с GPS-трекингом', 'benefit'),
            ('pod_rate', 'Доля рейсов с POD', 'benefit'),
            ('feedback_score', 'Средняя оценка клиентов', 'benefit'),
            ('rate_per_km', 'Средняя ставка за километр', 'cost'),
        ]
        for order, (code, name, kind) in enumerate(criteria, 1):
            _db.session.add(Criterion(code=code, name=name, kind=kind, order_no=order))
        _db.session.commit()

        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()