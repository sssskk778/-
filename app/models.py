# app/models.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# ПОЛЬЗОВАТЕЛИ
# =============================================================================

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, value: str):
        self.password_hash = generate_password_hash(value)

    def check_password(self, value: str) -> bool:
        return check_password_hash(self.password_hash, value)


# =============================================================================
# ДАТАСЕТЫ
# =============================================================================

class Dataset(db.Model, TimestampMixin):
    __tablename__ = 'datasets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    file_name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    records_count = db.Column(db.Integer, default=0, nullable=False)


# =============================================================================
# КРИТЕРИИ
# =============================================================================

class Criterion(db.Model):
    __tablename__ = 'criteria'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=False, unique=True)
    name = db.Column(db.String(160), nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # 'benefit' или 'cost'
    order_no = db.Column(db.Integer, nullable=False)


# =============================================================================
# ДАННЫЕ ДЛЯ РАСЧЁТА KPI
# =============================================================================

# =============================================================================
# ДАННЫЕ ДЛЯ РАСЧЁТА KPI
# =============================================================================

class Carrier(db.Model, TimestampMixin):
    __tablename__ = 'carriers'
    carrier_id = db.Column(db.BigInteger, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=True)  # ← ВЕРНУТЬ
    name = db.Column(db.Text, nullable=False)
    inn = db.Column(db.String(20), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    fleet_type = db.Column(db.String(50), nullable=True)
    dataset = db.relationship('Dataset', backref='carriers')  # ← ВЕРНУТЬ


class Shipment(db.Model, TimestampMixin):
    __tablename__ = 'shipments'
    shipment_id = db.Column(db.BigInteger, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=True)  # ← ВЕРНУТЬ
    carrier_id = db.Column(db.BigInteger, db.ForeignKey('carriers.carrier_id'), nullable=True)
    shipper_id = db.Column(db.BigInteger, nullable=True)
    origin = db.Column(db.Text, nullable=True)
    destination = db.Column(db.Text, nullable=True)
    pickup_window_start = db.Column(db.DateTime, nullable=True)
    pickup_window_end = db.Column(db.DateTime, nullable=True)
    delivery_window_start = db.Column(db.DateTime, nullable=True)
    delivery_window_end = db.Column(db.DateTime, nullable=True)
    cargo_type = db.Column(db.Text, nullable=True)
    ordered_quantity = db.Column(db.Integer, nullable=True)
    delivered_quantity = db.Column(db.Integer, nullable=True)
    client_rating = db.Column(db.Integer, nullable=True)
    force_majeure = db.Column(db.Integer, default=0)
    dataset = db.relationship('Dataset', backref='shipments')  # ← ВЕРНУТЬ
    carrier = db.relationship('Carrier', backref='shipments')

class ShipmentEvent(db.Model):
    __tablename__ = 'shipment_events'
    event_id = db.Column(db.BigInteger, primary_key=True)
    shipment_id = db.Column(db.BigInteger, db.ForeignKey('shipments.shipment_id'), nullable=False)
    carrier_id = db.Column(db.BigInteger, db.ForeignKey('carriers.carrier_id'), nullable=True)
    event_type = db.Column(db.Text, nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    source = db.Column(db.Text, nullable=True)
    cancelled_by = db.Column(db.Text, nullable=True)
    is_carrier_fault = db.Column(db.Boolean, default=True)

    shipment = db.relationship('Shipment', backref='events')
    carrier = db.relationship('Carrier', backref='events')


class ShipmentDocument(db.Model):
    __tablename__ = 'shipment_documents'
    doc_id = db.Column(db.BigInteger, primary_key=True)
    shipment_id = db.Column(db.BigInteger, db.ForeignKey('shipments.shipment_id'), nullable=False)
    carrier_id = db.Column(db.BigInteger, db.ForeignKey('carriers.carrier_id'), nullable=True)
    doc_type = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=True)
    is_valid = db.Column(db.Boolean, default=True)
    payment_due_date = db.Column(db.Date, nullable=True)
    payment_actual_date = db.Column(db.Date, nullable=True)

    shipment = db.relationship('Shipment', backref='documents')
    carrier = db.relationship('Carrier', backref='documents')


class Claim(db.Model):
    __tablename__ = 'claims'
    claim_id = db.Column(db.BigInteger, primary_key=True)
    shipment_id = db.Column(db.BigInteger, db.ForeignKey('shipments.shipment_id'), nullable=False)
    carrier_id = db.Column(db.BigInteger, db.ForeignKey('carriers.carrier_id'), nullable=True)
    claim_type = db.Column(db.Text, nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    carrier_fault = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shipment = db.relationship('Shipment', backref='claims')
    carrier = db.relationship('Carrier', backref='claims')


class CarrierBehavior(db.Model):
    __tablename__ = 'carrier_behavior'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    carrier_id = db.Column(db.BigInteger, db.ForeignKey('carriers.carrier_id'), nullable=False)
    accepted = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    carrier = db.relationship('Carrier', backref='behaviors')


# =============================================================================
# СЦЕНАРИИ И РЕЗУЛЬТАТЫ
# =============================================================================

class Scenario(db.Model, TimestampMixin):
    __tablename__ = 'scenarios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    method = db.Column(db.String(30), nullable=False, default='topsis')
    weight_mode = db.Column(db.String(20), default='swara')  # 'manual' или 'swara'
    manual_weights_json = db.Column(db.Text, nullable=True)
    swara_config_json = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default='draft')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_by_user = db.relationship('User', backref='scenarios', foreign_keys=[created_by])

    def get_manual_weights(self):
        return json.loads(self.manual_weights_json) if self.manual_weights_json else {}

    def set_manual_weights(self, weights_dict):
        self.manual_weights_json = json.dumps(weights_dict)

    def get_swara_config(self):
        return json.loads(self.swara_config_json) if self.swara_config_json else {}

    def set_swara_config(self, ranking, s_values):
        self.swara_config_json = json.dumps({
            'ranking': ranking,
            's_values': s_values
        })


class ScenarioCriterion(db.Model):
    __tablename__ = 'scenario_criteria'
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), primary_key=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criteria.id'), primary_key=True)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    order_no = db.Column(db.Integer, nullable=False)


class Run(db.Model):
    __tablename__ = 'runs'
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=False)
    initiated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='created')
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    meta_json = db.Column(db.Text, nullable=True)


class RunResult(db.Model):
    __tablename__ = 'run_results'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('runs.id'), nullable=False)
    carrier_id = db.Column(db.BigInteger, db.ForeignKey('carriers.carrier_id'), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    details_json = db.Column(db.Text, nullable=True)