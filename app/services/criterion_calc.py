# app/services/criteria_calculator_v2.py
"""
Расчет 12 критериев оценки перевозчиков (с decay, внешними факторами)
БЕЗ нормализации — только сырые значения
БЕЗ DataLoader - прямые запросы к БД
"""
from datetime import datetime, timedelta
import numpy as np
from app import db
from app.models import Carrier, Shipment, ShipmentEvent, ShipmentDocument, Claim, CarrierBehavior


class CriteriaCalculator:
    """Калькулятор 12 критериев для перевозчиков (только сырые значения)"""

    def __init__(self, decay_halflife=90, window_days=180, verbose=True):
        self.decay_halflife = decay_halflife
        self.window_days = window_days
        self.today = datetime.now().date()
        self.cutoff_date = self.today - timedelta(days=window_days)
        self.carriers = []
        self.shipments = []
        self.verbose = verbose

    def _log(self, msg, indent=0):
        if self.verbose:
            print("  " * indent + str(msg))

    def _decay_weight(self, date_value):
        if date_value is None:
            return 0.0
        if isinstance(date_value, datetime):
            date_value = date_value.date()
        age_days = (self.today - date_value).days
        if age_days > self.window_days:
            return 0.0
        if age_days < 0:
            age_days = 0
        weight = 0.5 ** (age_days / self.decay_halflife)
        return weight

    def _is_force_majeure(self, shipment):
        if not shipment:
            return False
        return shipment.force_majeure == 1

    def load_data(self):
        self.carriers = Carrier.query.all()
        self.shipments = Shipment.query.all()
        self._log(f"📦 Загружено перевозчиков: {len(self.carriers)}")
        self._log(f"📦 Загружено рейсов: {len(self.shipments)}")
        self._log(f"📅 Сегодня: {self.today}")
        self._log(f"📅 Cutoff date (6 месяцев назад): {self.cutoff_date}")
        return self

    # =========================================================================
    # ПРЯМЫЕ ЗАПРОСЫ К БД
    # =========================================================================

    def _get_events(self, shipment_id):
        return ShipmentEvent.query.filter_by(shipment_id=shipment_id).all()

    def _get_event_by_type(self, shipment_id, event_type):
        return ShipmentEvent.query.filter_by(
            shipment_id=shipment_id,
            event_type=event_type
        ).first()

    def _count_gps_events(self, shipment_id):
        return ShipmentEvent.query.filter_by(
            shipment_id=shipment_id,
            source='gps'
        ).count()

    def _get_claims(self, shipment_id):
        return Claim.query.filter_by(shipment_id=shipment_id).all()

    def _has_valid_pod(self, shipment_id):
        pod = ShipmentDocument.query.filter_by(
            shipment_id=shipment_id,
            doc_type='POD',
            is_valid=True
        ).first()
        return pod is not None

    def _get_behaviors(self, carrier_id):
        return CarrierBehavior.query.filter_by(carrier_id=carrier_id).all()

    # =========================================================================
    # ОСНОВНОЙ МЕТОД — ТОЛЬКО СЫРЫЕ ЗНАЧЕНИЯ
    # =========================================================================

    def calculate_all(self):
        """
        Возвращает ТОЛЬКО сырые значения критериев для всех перевозчиков.
        Нормализацию нужно делать отдельно перед подачей в TOPSIS/VIKOR.
        """
        self._log("\n" + "=" * 80)
        self._log("🧮 НАЧАЛО РАСЧЁТА СЫРЫХ КРИТЕРИЕВ")
        self._log("=" * 80)

        results = {}
        for carrier in self.carriers:
            self._log(f"\n🚚 Перевозчик: {carrier.name} (ID={carrier.carrier_id})")
            carrier_shipments = [s for s in self.shipments if s.carrier_id == carrier.carrier_id]
            self._log(f"   Рейсов всего: {len(carrier_shipments)}")
            raw_criteria = self._calculate_raw_criteria(carrier.carrier_id, carrier_shipments)
            results[carrier.carrier_id] = {
                'company_name': carrier.name,
                'criteria_raw': raw_criteria
            }
            self._log(f"   Сырые критерии: {raw_criteria}")

        return results

    def _calculate_raw_criteria(self, carrier_id, shipments):
        criteria = {}
        criteria['otif'] = self._calc_otif(shipments, carrier_id)
        criteria['cancellation_rate'] = self._calc_cancellation_rate(shipments, carrier_id)
        criteria['no_show_rate'] = self._calc_no_show_rate(shipments, carrier_id)
        criteria['damage_rate'] = self._calc_damage_rate(shipments, carrier_id)
        criteria['claim_rate'] = self._calc_claim_rate(shipments, carrier_id)
        criteria['tracking_compliance'] = self._calc_tracking_compliance(shipments, carrier_id)
        criteria['pod_rate'] = self._calc_pod_rate(shipments, carrier_id)
        criteria['payment_compliance'] = self._calc_payment_compliance(carrier_id)
        criteria['acceptance_rate'] = self._calc_acceptance_rate(carrier_id)
        criteria['rejection_rate'] = self._calc_rejection_rate(carrier_id)
        criteria['repeat_order_rate'] = self._calc_repeat_order_rate(shipments, carrier_id)
        criteria['feedback_score'] = self._calc_feedback_score(shipments, carrier_id)
        return criteria

    # =========================================================================
    # ГРУППА 1: НАДЁЖНОСТЬ И КАЧЕСТВО ДОСТАВКИ (5 KPI)
    # =========================================================================

    def _calc_otif(self, shipments, carrier_id):
        completed = [
            s for s in shipments
            if s.delivery_window_end and s.delivery_window_end.date() >= self.cutoff_date
        ]

        if carrier_id in [1006, 1007]:
            self._log(f"   [OTIF] Всего рейсов: {len(shipments)}, в окне: {len(completed)}", indent=1)

        if not completed:
            return 0.0

        total_weight = 0.0
        weighted_otif = 0.0

        for s in completed:
            weight = self._decay_weight(s.delivery_window_end)
            if weight == 0:
                continue
            total_weight += weight

            delivery_event = self._get_event_by_type(s.shipment_id, 'DELIVERED')
            if not delivery_event:
                continue

            on_time = (
                    s.delivery_window_end and
                    delivery_event.event_time and
                    delivery_event.event_time <= s.delivery_window_end
            )
            in_full = (
                    s.ordered_quantity and
                    s.delivered_quantity and
                    s.delivered_quantity >= s.ordered_quantity
            )

            if self._is_force_majeure(s):
                weighted_otif += weight
            elif on_time and in_full:
                weighted_otif += weight

        result = round(weighted_otif / total_weight * 100, 2) if total_weight else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [OTIF] Результат: {result}%", indent=1)
        return result

    def _calc_cancellation_rate(self, shipments, carrier_id):
        confirmed = [
            s for s in shipments
            if s.pickup_window_start and s.pickup_window_start.date() >= self.cutoff_date
        ]
        if not confirmed:
            return 0.0

        total_weight = 0.0
        weighted_cancelled = 0.0

        for s in confirmed:
            weight = self._decay_weight(s.pickup_window_start)
            if weight == 0:
                continue
            total_weight += weight

            if self._is_force_majeure(s):
                continue

            cancel_event = self._get_event_by_type(s.shipment_id, 'CANCELLED')
            if cancel_event and getattr(cancel_event, 'cancelled_by', None) == 'carrier':
                weighted_cancelled += weight
                if carrier_id in [1006, 1007]:
                    self._log(f"   [CANCEL] shipment {s.shipment_id} отменён перевозчиком", indent=1)

        rate = (weighted_cancelled / total_weight * 100) if total_weight else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [CANCEL] Результат: {rate:.2f}%", indent=1)
        return round(rate, 2)

    def _calc_no_show_rate(self, shipments, carrier_id):
        confirmed = [
            s for s in shipments
            if s.pickup_window_start and s.pickup_window_start.date() >= self.cutoff_date
        ]
        if not confirmed:
            return 0.0

        total_weight = 0.0
        weighted_no_show = 0.0

        for s in confirmed:
            weight = self._decay_weight(s.pickup_window_start)
            if weight == 0:
                continue
            total_weight += weight

            if self._is_force_majeure(s):
                continue

            if self._get_event_by_type(s.shipment_id, 'NO_SHOW'):
                weighted_no_show += weight
                if carrier_id in [1006, 1007]:
                    self._log(f"   [NO_SHOW] shipment {s.shipment_id} неявка", indent=1)

        rate = (weighted_no_show / total_weight * 100) if total_weight else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [NO_SHOW] Результат: {rate:.2f}%", indent=1)
        return round(rate, 2)

    def _calc_damage_rate(self, shipments, carrier_id):
        completed = [
            s for s in shipments
            if s.delivery_window_end and s.delivery_window_end.date() >= self.cutoff_date
        ]
        if not completed:
            return 0.0

        total_weight = 0.0
        weighted_damaged = 0.0

        for s in completed:
            weight = self._decay_weight(s.delivery_window_end)
            if weight == 0:
                continue
            total_weight += weight

            if self._is_force_majeure(s):
                continue

            claims = self._get_claims(s.shipment_id)
            for claim in claims:
                if claim.claim_type == 'DAMAGE' and getattr(claim, 'carrier_fault', False):
                    weighted_damaged += weight
                    if carrier_id in [1006, 1007]:
                        self._log(f"   [DAMAGE] shipment {s.shipment_id} повреждение по вине", indent=1)
                    break

        rate = (weighted_damaged / total_weight * 100) if total_weight else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [DAMAGE] Результат: {rate:.2f}%", indent=1)
        return round(rate, 2)

    def _calc_claim_rate(self, shipments, carrier_id):
        completed = [
            s for s in shipments
            if s.delivery_window_end and s.delivery_window_end.date() >= self.cutoff_date
        ]
        if not completed:
            return 0.0

        shipments_with_claims = 0
        for s in completed:
            if self._get_claims(s.shipment_id):
                shipments_with_claims += 1

        rate = (shipments_with_claims / len(completed) * 100) if completed else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [CLAIM] Результат: {rate:.2f}%", indent=1)
        return round(rate, 2)

    def _calc_tracking_compliance(self, shipments, carrier_id):
        completed = [
            s for s in shipments
            if s.pickup_window_start and s.pickup_window_start.date() >= self.cutoff_date
        ]
        if not completed:
            return 0.0

        total_weight = 0.0
        weighted_tracked = 0.0

        for s in completed:
            weight = self._decay_weight(s.pickup_window_start)
            if weight == 0:
                continue
            total_weight += weight

            if self._is_force_majeure(s):
                continue

            gps_count = self._count_gps_events(s.shipment_id)
            if gps_count > 0:
                weighted_tracked += weight

        result = round(weighted_tracked / total_weight * 100, 2) if total_weight else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [GPS] Результат: {result}%", indent=1)
        return result

    def _calc_pod_rate(self, shipments, carrier_id):
        completed = [
            s for s in shipments
            if s.delivery_window_end and s.delivery_window_end.date() >= self.cutoff_date
        ]
        if not completed:
            return 0.0

        total_weight = 0.0
        weighted_pod = 0.0

        for s in completed:
            weight = self._decay_weight(s.delivery_window_end)
            if weight == 0:
                continue
            total_weight += weight

            if self._has_valid_pod(s.shipment_id):
                weighted_pod += weight

        result = round(weighted_pod / total_weight * 100, 2) if total_weight else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [POD] Результат: {result}%", indent=1)
        return result

    def _calc_payment_compliance(self, carrier_id):
        invoices = ShipmentDocument.query.filter_by(
            carrier_id=carrier_id,
            doc_type='INVOICE'
        ).filter(
            ShipmentDocument.payment_due_date.isnot(None)
        ).all()

        if not invoices:
            return 0.0

        overdue = 0
        for inv in invoices:
            if inv.payment_actual_date is None:
                if inv.payment_due_date < self.today:
                    overdue += 1
            elif inv.payment_actual_date > inv.payment_due_date:
                overdue += 1

        rate = (overdue / len(invoices) * 100) if invoices else 0.0
        return round(rate, 2)

    def _calc_acceptance_rate(self, carrier_id):
        behaviors = self._get_behaviors(carrier_id)
        if not behaviors:
            return 0.0
        accepted = sum(1 for b in behaviors if b.accepted)
        return round(accepted / len(behaviors) * 100, 2)

    def _calc_rejection_rate(self, carrier_id):
        behaviors = self._get_behaviors(carrier_id)
        if not behaviors:
            return 0.0
        rejected = sum(1 for b in behaviors if b.rejected)
        return round(rejected / len(behaviors) * 100, 2)

    def _calc_repeat_order_rate(self, shipments, carrier_id):
        completed = [
            s for s in shipments
            if s.delivery_window_end and s.delivery_window_end.date() >= self.cutoff_date
        ]
        if not completed:
            return 0.0

        shipper_counts = {}
        for s in completed:
            if s.shipper_id:
                shipper_counts[s.shipper_id] = shipper_counts.get(s.shipper_id, 0) + 1

        repeat_shipments = sum(count for count in shipper_counts.values() if count >= 2)
        rate = (repeat_shipments / len(completed) * 100) if completed else 0.0
        if carrier_id in [1006, 1007]:
            self._log(f"   [REPEAT] Повторных рейсов: {repeat_shipments} из {len(completed)}", indent=1)
        return round(rate, 2)

    def _calc_feedback_score(self, shipments, carrier_id):
        rated = [
            s for s in shipments
            if s.delivery_window_end and s.delivery_window_end.date() >= self.cutoff_date and s.client_rating
        ]
        if not rated:
            return 3.0

        total_weight = 0.0
        weighted_rating = 0.0

        for s in rated:
            weight = self._decay_weight(s.delivery_window_end)
            if weight == 0:
                continue
            total_weight += weight
            weighted_rating += s.client_rating * weight

        return round(weighted_rating / total_weight, 2) if total_weight else 3.0

    # =========================================================================
    # API методы
    # =========================================================================

    def get_criteria_names_short(self):
        return [
            'otif', 'cancellation_rate', 'no_show_rate',
            'damage_rate', 'claim_rate', 'tracking_compliance', 'pod_rate',
            'payment_compliance', 'acceptance_rate', 'rejection_rate',
            'repeat_order_rate', 'feedback_score'
        ]

    def get_criteria_names(self):
        return [
            'OTIF', 'Отмены рейсов', 'Неявка',
            'Повреждения груза', 'Частота претензий', 'GPS трекинг',
            'Подтверждение доставки', 'Просрочка платежей',
            'Принятие заказов', 'Отказы от заявок',
            'Повторные рейсы', 'Отзывы клиентов'
        ]

    def get_criteria_kinds(self):
        return [
            'benefit', 'cost', 'cost',
            'cost', 'cost', 'benefit', 'benefit',
            'cost', 'benefit', 'cost',
            'benefit', 'benefit'
        ]

    def get_criteria_kinds_dict(self):
        names = self.get_criteria_names_short()
        kinds = self.get_criteria_kinds()
        return dict(zip(names, kinds))

    def get_raw_matrix(self):
        """
        Возвращает матрицу СЫРЫХ значений критериев.
        Строки — перевозчики, столбцы — критерии.
        """
        results = self.calculate_all()
        carriers_list = []
        matrix = []

        for carrier_id, data in results.items():
            carriers_list.append({
                'carrier_id': carrier_id,
                'company_name': data['company_name']
            })
            row = [data['criteria_raw'][code] for code in self.get_criteria_names_short()]
            matrix.append(row)

        return np.array(matrix), carriers_list