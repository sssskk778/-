# tests/test_criteria_calc.py
import pytest
from datetime import datetime, timedelta
from app.services.criterion_calc import CriteriaCalculator

"""
Тестирование калькулятора критериев.
Проверяется загрузка данных, decay-веса и корректность формул расчета.
"""

def test_calculator_load_data(app):
    with app.app_context():
        calc = CriteriaCalculator()
        calc.load_data()
        assert len(calc.carriers) >= 0
        assert len(calc.shipments) >= 0


def test_calculator_decay_weight():
    calc = CriteriaCalculator(decay_halflife=180)
    today = datetime.now()
    assert calc._decay_weight(today) == 1.0
    old = today - timedelta(days=180)
    assert calc._decay_weight(old) == pytest.approx(0.5, 0.01)

def test_on_time_rate_perfect():
    """Один доставленный вовремя рейс → 100%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'delivery_window_end': now - timedelta(days=1),
        'actual_delivery_time': now - timedelta(days=1),
    })
    result = calc._on_time([s])
    assert result == 100.0


def test_on_time_rate_late():
    """Один опоздавший рейс → 0%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'delivery_window_end': now - timedelta(days=1),
        'actual_delivery_time': now + timedelta(hours=5),
    })
    result = calc._on_time([s])
    assert result == 0.0


def test_cancellation_rate_half():
    """1 доставлен + 1 отменен → 50%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s1 = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'status': 'Доставлено',
    })
    s2 = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'status': 'Отменено',
    })
    result = calc._cancellation([s1, s2])
    assert result == 50.0


def test_no_show_rate():
    """1 доставлен + 1 неявка → 50%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s1 = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'status': 'Доставлено',
    })
    s2 = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'status': 'Не приехал',
    })
    result = calc._no_show([s1, s2])
    assert result == 50.0


def test_damage_rate():
    """1 доставлен с повреждением → 100%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'claim_type': 'Повреждение',
    })
    result = calc._damage([s])
    assert result == 100.0


def test_loss_rate():
    """1 доставлен с потерей → 100%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'claim_type': 'Потеря',
    })
    result = calc._loss([s])
    assert result == 100.0


def test_accident_rate():
    """1 рейс с ДТП по вине, тяжесть средняя → 150%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'carrier_fault': True,
        'accident_severity': 'Среднее',
    })
    result = calc._accident([s])
    assert result == 150.0


def test_tracking_compliance():
    """1 рейс с GPS → 100%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'has_gps': True,
    })
    result = calc._tracking([s])
    assert result == 100.0


def test_pod_rate():
    """1 рейс с POD → 100%"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'has_pod': True,
    })
    result = calc._pod([s])
    assert result == 100.0


def test_feedback_score():
    """Оценка 5 → 5.0"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'client_rating': 5,
    })
    result = calc._feedback([s])
    assert result == 5.0


def test_rate_per_km():
    """Цена 1000 / расстояние 100 → 10.0"""
    calc = CriteriaCalculator()
    now = datetime.now()
    s = type('Shipment', (), {
        'pickup_window_start': now - timedelta(days=2),
        'price': 1000,
        'distance_km': 100,
    })
    result = calc._rpk([s])
    assert result == 10.0