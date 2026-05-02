# tests/test_models.py
import pytest
import random
from app import db
from app.models import User, Dataset, Carrier, Shipment, Scenario, Run, RunResult

"""
Тестирование моделей базы данных.
Проверяется создание записей, уникальность полей и связи между таблицами.
"""

def test_create_user(app):
    """
    - Тестируется создание пользователя
    - Проверяется сохранение в БД и проверка пароля
    - Пользователь должен быть найден, пароль верный
    """
    uid = random.randint(10000, 99999)
    with app.app_context():
        # Arrange
        user = User(username=f'test{uid}', full_name='Test', role='user')
        user.set_password('123456')
        # Act
        db.session.add(user)
        db.session.commit()
        saved = User.query.filter_by(username=f'test{uid}').first()
        # Assert
        assert saved is not None
        assert saved.check_password('123456') == True
        assert saved.check_password('wrong') == False


def test_user_unique_username(app):
    """
    - Тестируется уникальность логина пользователя
    - Проверяется выброс исключения при дублировании
    """
    uid = random.randint(10000, 99999)
    with app.app_context():
        # Arrange
        u1 = User(username=f'uniq{uid}', full_name='A', role='user')
        u1.set_password('123456')
        db.session.add(u1)
        db.session.commit()
        u2 = User(username=f'uniq{uid}', full_name='B', role='user')
        u2.set_password('123456')
        db.session.add(u2)
        # Act & Assert
        with pytest.raises(Exception):
            db.session.commit()


def test_create_dataset(app):
    """
    - Тестируется создание датасета
    - Проверяется сохранение в БД
    - ID должен быть присвоен, имя сохранено
    """
    with app.app_context():
        # Arrange
        ds = Dataset(name='Test', file_name='test.xlsx', records_count=10)
        # Act
        db.session.add(ds)
        db.session.commit()
        # Assert
        assert ds.id is not None
        assert ds.name == 'Test'


def test_create_carrier(app):
    """
    - Тестируется создание перевозчика
    - Проверяется сохранение в БД
    """
    cid = random.randint(10000, 99999)
    with app.app_context():
        # Arrange
        c = Carrier(carrier_id=cid, company_name='Test', fleet_type='бортовые', region='Южный')
        # Act
        db.session.add(c)
        db.session.commit()
        # Assert
        assert db.session.get(Carrier, cid) is not None


def test_create_shipment(app):
    """
    - Тестируется создание рейса
    - Проверяется сохранение в БД со связями
    """
    sid = random.randint(10000, 99999)
    cid = random.randint(10000, 99999)
    with app.app_context():
        # Arrange
        ds = Dataset(name='Test', records_count=1)
        db.session.add(ds)
        db.session.flush()
        c = Carrier(carrier_id=cid, company_name='Test')
        db.session.add(c)
        db.session.flush()
        s = Shipment(shipment_id=sid, dataset_id=ds.id, carrier_id=c.carrier_id,
                     status='Доставлено', client_rating=5, price=1000, distance_km=100)
        # Act
        db.session.add(s)
        db.session.commit()
        # Assert
        assert db.session.get(Shipment, sid) is not None


def test_scenario_swara_config(app):
    """
    - Тестируется сохранение и загрузка конфигурации SWARA
    - Проверяется JSON-сериализация
    """
    with app.app_context():
        # Arrange
        s = Scenario(name='Test', method='topsis', status='draft')
        s.set_swara_config(['a', 'b'], [0.5])
        # Act
        db.session.add(s)
        db.session.commit()
        config = s.get_swara_config()
        # Assert
        assert config['ranking'] == ['a', 'b']
        assert config['s_values'] == [0.5]


def test_run_result(app):
    with app.app_context():
        # Arrange — берём существующего админа
        u = User.query.filter_by(username='admin').first()
        s = Scenario(name='Test', created_by=u.id)
        db.session.add(s)
        db.session.flush()
        r = Run(scenario_id=s.id, initiated_by=u.id, status='done')
        db.session.add(r)
        db.session.flush()
        cid = random.randint(10000, 99999)
        c = Carrier(carrier_id=cid, company_name='Test')
        db.session.add(c)
        db.session.flush()
        # Act
        rr = RunResult(run_id=r.id, carrier_id=c.carrier_id, rank=1, score=0.95)
        db.session.add(rr)
        db.session.commit()
        # Assert
        assert RunResult.query.filter_by(run_id=r.id).first() is not None