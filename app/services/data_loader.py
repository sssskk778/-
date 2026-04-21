# app/services/data_loader.py
"""
Предзагрузка и кэширование данных для CriteriaCalculatorV2

from app.models import (
    ShipmentEvent, Claim, ShipmentDocument, CarrierBehavior
)


class DataLoader:
    Класс для предзагрузки и кэширования связанных данных

    def __init__(self, shipments, cutoff_date):
        self.shipments = shipments
        self.cutoff_date = cutoff_date

        # Кэши для быстрого доступа
        self.events_cache = {}
        self.claims_cache = {}
        self.documents_cache = {}
        self.behaviors_cache = {}
        self.all_claims_cache = {}  # все претензии по carrier_id

    def preload_all(self, carrier_ids):
        Загружает все связанные данные в кэши
        self._preload_events()
        self._preload_claims()
        self._preload_documents()
        self._preload_behaviors(carrier_ids)
        self._preload_all_claims(carrier_ids)

    # -------------------------------------------------------------------------
    # События
    # -------------------------------------------------------------------------
    def _preload_events(self):
        shipment_ids = [s.shipment_id for s in self.shipments if s.shipment_id]
        if not shipment_ids:
            return
        all_events = ShipmentEvent.query.filter(
            ShipmentEvent.shipment_id.in_(shipment_ids)
        ).all()
        for event in all_events:
            if event.shipment_id not in self.events_cache:
                self.events_cache[event.shipment_id] = []
            self.events_cache[event.shipment_id].append(event)

    def get_events(self, shipment_id):
        return self.events_cache.get(shipment_id, [])

    def get_event_by_type(self, shipment_id, event_type):
        for event in self.get_events(shipment_id):
            if event.event_type == event_type:
                return event
        return None

    def count_gps_events(self, shipment_id):
        return sum(1 for e in self.get_events(shipment_id) if e.source == 'gps')

    # -------------------------------------------------------------------------
    # Претензии
    # -------------------------------------------------------------------------
    def _preload_claims(self):
        shipment_ids = [s.shipment_id for s in self.shipments if s.shipment_id]
        if not shipment_ids:
            return
        all_claims = Claim.query.filter(
            Claim.shipment_id.in_(shipment_ids)
        ).all()
        for claim in all_claims:
            if claim.shipment_id not in self.claims_cache:
                self.claims_cache[claim.shipment_id] = []
            self.claims_cache[claim.shipment_id].append(claim)

    def get_claims(self, shipment_id):
        return self.claims_cache.get(shipment_id, [])

    def has_claim(self, shipment_id):
        return len(self.get_claims(shipment_id)) > 0

    def has_damage_claim(self, shipment_id):
        for claim in self.get_claims(shipment_id):
            if claim.claim_type == 'DAMAGE':
                return True
        return False

    def has_unresolved_claim(self, shipment_id):
        for claim in self.get_claims(shipment_id):
            if not claim.resolved:
                return True
        return False

    def _preload_all_claims(self, carrier_ids):

        if not carrier_ids:
            return
        all_claims = Claim.query.filter(
            Claim.carrier_id.in_(carrier_ids)
        ).all()
        for claim in all_claims:
            if claim.carrier_id not in self.all_claims_cache:
                self.all_claims_cache[claim.carrier_id] = []
            self.all_claims_cache[claim.carrier_id].append(claim)

    def get_all_claims_for_carrier(self, carrier_id):
        return self.all_claims_cache.get(carrier_id, [])

    # -------------------------------------------------------------------------
    # Документы
    # -------------------------------------------------------------------------
    def _preload_documents(self):
        shipment_ids = [s.shipment_id for s in self.shipments if s.shipment_id]
        if not shipment_ids:
            return
        all_docs = ShipmentDocument.query.filter(
            ShipmentDocument.shipment_id.in_(shipment_ids)
        ).all()
        for doc in all_docs:
            if doc.shipment_id not in self.documents_cache:
                self.documents_cache[doc.shipment_id] = []
            self.documents_cache[doc.shipment_id].append(doc)

    def get_documents(self, shipment_id):
        return self.documents_cache.get(shipment_id, [])

    def has_valid_pod(self, shipment_id):
        for doc in self.get_documents(shipment_id):
            if doc.doc_type == 'POD' and doc.is_valid:
                return True
        return False

    # -------------------------------------------------------------------------
    # Поведение перевозчиков
    # -------------------------------------------------------------------------
    def _preload_behaviors(self, carrier_ids):
        if not carrier_ids:
            return
        all_behaviors = CarrierBehavior.query.filter(
            CarrierBehavior.carrier_id.in_(carrier_ids)
        ).all()  # ← убрал фильтр по created_at
        for b in all_behaviors:
            if b.carrier_id not in self.behaviors_cache:
                self.behaviors_cache[b.carrier_id] = []
            self.behaviors_cache[b.carrier_id].append(b)

    def get_behaviors(self, carrier_id):
        return self.behaviors_cache.get(carrier_id, []) """