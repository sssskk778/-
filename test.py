# test_calc.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app import create_app, db
from app.models import Carrier, Shipment, ShipmentEvent, ShipmentDocument, Claim, CarrierBehavior
from app.services.criterion_calc import CriteriaCalculator

# Создаём приложение без аргументов
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['TESTING'] = True

with app.app_context():
    db.create_all()

    # Загружаем тестовые данные
    print("📦 Создание тестовых данных...")

    # Идеальный
    db.session.add(Carrier(carrier_id=1006, name='Идеальный'))
    db.session.add(Carrier(carrier_id=1007, name='Плохой'))

    # Рейсы идеального
    db.session.add(Shipment(
        shipment_id=1, carrier_id=1006, shipper_id=5011,
        pickup_window_start=datetime(2026, 3, 1, 10, 0),
        pickup_window_end=datetime(2026, 3, 1, 12, 0),
        delivery_window_start=datetime(2026, 3, 2, 8, 0),
        delivery_window_end=datetime(2026, 3, 2, 14, 0),
        ordered_quantity=10, delivered_quantity=10, client_rating=5, force_majeure=0
    ))
    db.session.add(Shipment(
        shipment_id=2, carrier_id=1006, shipper_id=5011,
        pickup_window_start=datetime(2026, 3, 5, 8, 0),
        pickup_window_end=datetime(2026, 3, 5, 10, 0),
        delivery_window_start=datetime(2026, 3, 6, 8, 0),
        delivery_window_end=datetime(2026, 3, 6, 18, 0),
        ordered_quantity=5, delivered_quantity=5, client_rating=5, force_majeure=0
    ))

    # Рейсы плохого
    db.session.add(Shipment(
        shipment_id=3, carrier_id=1007, shipper_id=5014,
        pickup_window_start=datetime(2026, 3, 1, 9, 0),
        pickup_window_end=datetime(2026, 3, 1, 11, 0),
        delivery_window_start=datetime(2026, 3, 2, 8, 0),
        delivery_window_end=datetime(2026, 3, 2, 18, 0),
        ordered_quantity=45, delivered_quantity=30, client_rating=1, force_majeure=0
    ))
    db.session.add(Shipment(
        shipment_id=4, carrier_id=1007, shipper_id=5015,
        pickup_window_start=datetime(2026, 3, 5, 8, 0),
        pickup_window_end=datetime(2026, 3, 5, 10, 0),
        delivery_window_start=datetime(2026, 3, 5, 18, 0),
        delivery_window_end=datetime(2026, 3, 5, 22, 0),
        ordered_quantity=30, delivered_quantity=20, client_rating=2, force_majeure=0
    ))
    db.session.commit()

    # События
    db.session.add(ShipmentEvent(event_id=1, shipment_id=1, carrier_id=1006, event_type='DELIVERED',
                                 event_time=datetime(2026, 3, 2, 10, 0), source='gps'))
    db.session.add(ShipmentEvent(event_id=2, shipment_id=2, carrier_id=1006, event_type='DELIVERED',
                                 event_time=datetime(2026, 3, 6, 12, 0), source='gps'))
    db.session.add(ShipmentEvent(event_id=3, shipment_id=3, carrier_id=1007, event_type='DELIVERED',
                                 event_time=datetime(2026, 3, 2, 20, 0), source='gps'))
    db.session.add(ShipmentEvent(event_id=4, shipment_id=3, carrier_id=1007, event_type='ACCIDENT',
                                 event_time=datetime(2026, 3, 2, 9, 0), source='manual', is_carrier_fault=True))
    db.session.add(ShipmentEvent(event_id=5, shipment_id=4, carrier_id=1007, event_type='NO_SHOW',
                                 event_time=datetime(2026, 3, 5, 11, 0), source='manual'))

    # Документы
    db.session.add(ShipmentDocument(doc_id=1, shipment_id=1, carrier_id=1006, doc_type='POD', is_valid=True))
    db.session.add(ShipmentDocument(doc_id=2, shipment_id=2, carrier_id=1006, doc_type='POD', is_valid=True))
    db.session.add(ShipmentDocument(doc_id=3, shipment_id=3, carrier_id=1007, doc_type='POD', is_valid=False))

    # Претензии
    db.session.add(
        Claim(claim_id=1, shipment_id=3, carrier_id=1007, claim_type='DAMAGE', resolved=True, carrier_fault=True))

    # Поведение
    db.session.add(CarrierBehavior(carrier_id=1006, accepted=True, rejected=False))
    db.session.add(CarrierBehavior(carrier_id=1006, accepted=True, rejected=False))
    db.session.add(CarrierBehavior(carrier_id=1007, accepted=False, rejected=True))
    db.session.add(CarrierBehavior(carrier_id=1007, accepted=True, rejected=False))
    db.session.commit()

    print("✅ Данные созданы")

    # Запускаем калькулятор
    print("\n🧮 Расчёт критериев...")
    calc = CriteriaCalculator()
    calc.today = datetime(2026, 4, 20).date()
    calc.cutoff_date = calc.today - timedelta(days=180)
    calc.load_data()
    results = calc.calculate_all()

    # Проверяем результаты
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)

    for carrier_id, data in results.items():
        print(f"\n{data['company_name']} (ID={carrier_id}):")
        print("-" * 40)
        for code, value in data['criteria_raw'].items():
            norm = data['criteria'][code]
            print(f"  {code:<20}: raw={value:>6.2f}, norm={norm:>6.4f}")

    # Проверки
    print("\n" + "=" * 60)
    print("ПРОВЕРКИ")
    print("=" * 60)

    ideal = results[1006]
    bad = results[1007]

    tests = [
        ("OTIF идеального = 100", ideal['criteria_raw']['otif'] == 100.0),
        ("OTIF плохого < 100", bad['criteria_raw']['otif'] < 100.0),
        ("POD Rate идеального = 100", ideal['criteria_raw']['pod_rate'] == 100.0),
        ("POD Rate плохого = 0", bad['criteria_raw']['pod_rate'] == 0.0),
        ("Acceptance Rate идеального = 100", ideal['criteria_raw']['acceptance_rate'] == 100.0),
        ("Acceptance Rate плохого = 50", bad['criteria_raw']['acceptance_rate'] == 50.0),
        ("Rejection Rate идеального = 0", ideal['criteria_raw']['rejection_rate'] == 0.0),
        ("Rejection Rate плохого = 50", bad['criteria_raw']['rejection_rate'] == 50.0),
        ("Feedback идеального = 5.0", ideal['criteria_raw']['feedback_score'] == 5.0),
        ("Feedback плохого < 3.0", bad['criteria_raw']['feedback_score'] < 3.0),
        ("Tracking идеального = 100", ideal['criteria_raw']['tracking_compliance'] == 100.0),
        ("No-show плохого > 0", bad['criteria_raw']['no_show_rate'] > 0.0),
        ("Damage плохого > 0", bad['criteria_raw']['damage_rate'] > 0.0),
        ("Claim плохого > 0", bad['criteria_raw']['claim_rate'] > 0.0),
        ("Repeat идеального > 0", ideal['criteria_raw']['repeat_order_rate'] > 0.0),
    ]

    passed = 0
    for desc, result in tests:
        status = "✅" if result else "❌"
        print(f"{status} {desc}")
        if result:
            passed += 1

    print(f"\nПройдено: {passed}/{len(tests)}")

    db.drop_all()