# tests/test_run_service.py
"""
Тестирование сервиса запуска расчетов.
Проверяется создание сценария и выполнение расчета.
"""
import pytest
from app import db
from app.services.core.run_service import RunService
from app.models import User, Scenario, ScenarioCriterion, Criterion, Carrier, Shipment


def test_create_scenario(app):
    """
    - Тестируется создание сценария
    - Проверяется что сценарий сохраняется в БД
    """
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        scenario = Scenario(name='Test Scenario', method='topsis', created_by=admin.id)
        db.session.add(scenario)
        db.session.commit()
        assert scenario.id is not None
        assert scenario.name == 'Test Scenario'


def test_add_criteria_to_scenario(app):
    """
    - Тестируется добавление критериев в сценарий
    - Проверяется что критерии привязываются
    """
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        scenario = Scenario(name='Test Criteria', method='topsis', created_by=admin.id)
        db.session.add(scenario)
        db.session.flush()

        criteria = Criterion.query.limit(2).all()
        for c in criteria:
            db.session.add(ScenarioCriterion(
                scenario_id=scenario.id,
                criterion_id=c.id,
                is_enabled=True,
                order_no=c.order_no
            ))
        db.session.commit()

        links = ScenarioCriterion.query.filter_by(scenario_id=scenario.id).all()
        assert len(links) == 2


def test_execute_run(app):
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        scenario = Scenario(name='Test Run', method='topsis', created_by=admin.id)
        db.session.add(scenario)
        db.session.flush()

        for c in Criterion.query.limit(2).all():
            db.session.add(ScenarioCriterion(
                scenario_id=scenario.id,
                criterion_id=c.id,
                is_enabled=True,
                order_no=c.order_no
            ))
        db.session.commit()

        # Добавляем перевозчика с доставленным рейсом
        import random
        cid = random.randint(10000, 99999)
        carrier = Carrier(carrier_id=cid, company_name='Test')
        db.session.add(carrier)
        db.session.flush()

        from datetime import datetime, timedelta
        now = datetime.now()
        shipment = Shipment(
            shipment_id=random.randint(10000, 99999),
            carrier_id=cid,
            status='Доставлено',
            pickup_window_start=now - timedelta(days=2),
            delivery_window_end=now - timedelta(days=1),
            actual_delivery_time=now - timedelta(days=1),
            client_rating=5,
            price=1000,
            distance_km=100,
            has_gps=True,
            has_pod=True,
            accident_severity='Нет',
            carrier_fault=False,
            claim_type='Нет'
        )
        db.session.add(shipment)
        db.session.commit()

        scenario.set_swara_config(['on_time_rate', 'cancellation_rate'], [0.2])
        db.session.commit()

        service = RunService()
        run = service.execute(scenario.id, admin.id)

        assert run is not None
        assert run.status == 'done'
        assert run.scenario_id == scenario.id
def test_execute_no_criteria_raises_error(app):
    """
    - Тестируется запуск расчета без критериев
    - Проверяется выброс ValueError
    """
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        scenario = Scenario(name='Test Empty', method='topsis', created_by=admin.id)
        db.session.add(scenario)
        db.session.commit()

        service = RunService()
        with pytest.raises(ValueError):
            service.execute(scenario.id, admin.id)


def test_latest_results_empty(app):
    """
    - Тестируется получение результатов для сценария без запусков
    - Проверяется возврат None, []
    """
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        scenario = Scenario(name='Test No Runs', method='topsis', created_by=admin.id)
        db.session.add(scenario)
        db.session.commit()

        service = RunService()
        run, results = service.latest_results(scenario.id)
        assert run is None
        assert results == []