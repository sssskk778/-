"""
Модуль сериализаторов — преобразование моделей БД в словари для JSON-ответов.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
import json

from app import db
from app.models import Dataset, Carrier, Shipment, Scenario, Run, RunResult, Criterion, ScenarioCriterion


def serialize_dataset(d: Dataset) -> dict:
    return {
        'id': d.id,
        'name': d.name,
        'file_name': d.file_name,
        'description': d.description,
        'records_count': d.records_count,
        'created_at': d.created_at.isoformat() if d.created_at else None,
    }


def serialize_carrier(c: Carrier) -> dict:
    return {
        'carrier_id': c.carrier_id,
        'company_name': c.company_name,
        'fleet_type': c.fleet_type,
        'region': c.region,
    }


def serialize_shipment(s: Shipment) -> dict:
    return {
        'shipment_id': s.shipment_id,
        'carrier_id': s.carrier_id,
        'dataset_id': s.dataset_id,
        'pickup_window_start': s.pickup_window_start.isoformat() if s.pickup_window_start else None,
        'delivery_window_end': s.delivery_window_end.isoformat() if s.delivery_window_end else None,
        'actual_delivery_time': s.actual_delivery_time.isoformat() if s.actual_delivery_time else None,
        'client_rating': s.client_rating,
        'price': float(s.price) if s.price else None,
        'distance_km': float(s.distance_km) if s.distance_km else None,
        'status': s.status,
        'has_gps': s.has_gps,
        'has_pod': s.has_pod,
        'accident_severity': s.accident_severity,
        'carrier_fault': s.carrier_fault,
        'claim_type': s.claim_type,
    }


def serialize_criterion(c: Criterion) -> dict:
    return {
        'id': c.id,
        'code': c.code,
        'name': c.name,
        'kind': c.kind,
        'order_no': c.order_no,
    }


def serialize_scenario(s: Scenario) -> dict:
    selected = (
        ScenarioCriterion.query
        .filter_by(scenario_id=s.id)
        .order_by(ScenarioCriterion.order_no.asc())
        .all()
    )
    criteria_objs = [db.session.get(Criterion, x.criterion_id) for x in selected]
    criteria_objs = [c for c in criteria_objs if c]
    return {
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'method': s.method,
        'status': s.status,
        'criterion_ids': [c.id for c in criteria_objs],
        'criteria': [serialize_criterion(c) for c in criteria_objs],
    }


def serialize_run(r: Run) -> dict:
    return {
        'id': r.id,
        'status': r.status,
        'started_at': r.started_at.isoformat() if r.started_at else None,
        'finished_at': r.finished_at.isoformat() if r.finished_at else None,
        'meta': json.loads(r.meta_json or '{}'),
    }


def serialize_run_result(r: RunResult) -> dict:
    return {
        'company_name': r.carrier.company_name,
        'carrier_id': r.carrier_id,
        'rank': r.rank,
        'score': r.score,
        'details': json.loads(r.details_json or '{}'),
    }