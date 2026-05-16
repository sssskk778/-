"""
Описание: Модуль расчета критериев оценки перевозчиков.
Содержит класс CriteriaCalculator, реализующий расчет 10 критериев
на основе исторических данных о рейсах с применением
экспоненциального временного взвешивания (decay) и корректирующих коэффициентов.
Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
from datetime import datetime
from app.models import Carrier, Shipment

ACCIDENT_SEVERITY_COEFFICIENTS = {
    'Легкое':  1.0,
    'Среднее': 1.5,
    'Тяжелое': 2.0,
}

class CriteriaCalculator:

    def __init__(self, decay_halflife=180):
        """
        Назначение:
            Создает объект калькулятора критериев.
        Параметры:
            decay_halflife (int): Период полураспада веса в днях.
        Возвращает:
            None.
        """
        self.decay_halflife = decay_halflife
        self.today = datetime.now().date()
        self.carriers = []
        self.shipments = []

    def _decay_weight(self, date_value):
        """
        Назначение:
            Вычисляет вес рейса по формуле линейного распада.
            S = max(s - max(0, |age - offset|) / s, 0)
            где s = scale / (1 - decay)
        Параметры:
            date_value (datetime): Дата погрузки рейса.
        Возвращает:
            float: Вес рейса от 0 до 1.
        """
        scale = 730  # горизонт 2 года в днях
        offset = 0  # льготный период без убывания
        decay = 0.5  # вес на границе scale (0.5 = половина веса через 2 года)

        age_days = (self.today - date_value.date()).days
        if age_days < 0:
            age_days = 0

        s = scale / (1.0 - decay)  # s = 730 / 0.5 = 1460
        return max(0.0, (s - max(0.0, age_days - offset)) / s)

    def load_data(self):
        """
        Назначение:
            Загружает всех перевозчиков и все рейсы из базы данных.
        Параметры:
            Нет.
        Возвращает:
            CriteriaCalculator: self.
        """
        self.carriers = Carrier.query.all()
        self.shipments = Shipment.query.all()
        return self

    def calculate_all(self):
        """
        Назначение:
            Выполняет расчет 10 критериев для всех перевозчиков.
            Перевозчики без доставленных рейсов пропускаются.
        Параметры:
            Нет.
        Возвращает:
            dict: {carrier_id: {company_name, criteria_raw}}.
        """
        results = {}

        for carrier in self.carriers:
            shipments = [s for s in self.shipments if s.carrier_id == carrier.carrier_id]
            delivered = [s for s in shipments if s.status == 'Доставлено']

            if not delivered:
                continue

            results[carrier.carrier_id] = {
                'company_name': carrier.company_name,
                'criteria_raw': {
                    'on_time_rate':        self._on_time(delivered),
                    'cancellation_rate':   self._cancellation(shipments),
                    'no_show_rate':        self._no_show(shipments),
                    'damage_rate':         self._damage(delivered),
                    'loss_rate':           self._loss(delivered),
                    'accident_rate':       self._accident(delivered),
                    'tracking_compliance': self._tracking(delivered),
                    'pod_rate':            self._pod(delivered),
                    'feedback_score':      self._feedback(delivered),
                    'rate_per_km':         self._rpk(delivered),
                }
            }

        return results

    def _on_time(self, delivered):
        """
        Назначение:
            Доля своевременных рейсов: actual_delivery_time <= delivery_window_end.
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        on_time = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.actual_delivery_time <= s.delivery_window_end:
                on_time += w
        return round(on_time / total * 100, 2)

    def _cancellation(self, shipments):
        """
        Назначение:
            Доля отмененных рейсов: status == 'Отменено'.
        Параметры:
            shipments (list[Shipment]): Все рейсы перевозчика.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        cancelled = 0.0
        for s in shipments:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.status == 'Отменено':
                cancelled += w
        return round(cancelled / total * 100, 2)

    def _no_show(self, shipments):
        """
        Назначение:
            Доля неявок: status == 'Не приехал'.
        Параметры:
            shipments (list[Shipment]): Все рейсы перевозчика.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        noshow = 0.0
        for s in shipments:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.status == 'Не приехал':
                noshow += w
        return round(noshow / total * 100, 2)

    def _damage(self, delivered):
        """
        Назначение:
            Доля рейсов с повреждением: claim_type == 'Повреждение'.
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        damage = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.claim_type == 'Повреждение':
                damage += w
        return round(damage / total * 100, 2)

    def _loss(self, delivered):
        """
        Назначение:
            Доля рейсов с утратой: claim_type == 'Потеря'.
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        loss = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.claim_type == 'Потеря':
                loss += w
        return round(loss / total * 100, 2)

    def _accident(self, delivered):
        """
        Назначение:
            Доля ДТП по вине перевозчика с учетом тяжести.
            Тяжесть: Легкое=1.0, Среднее=1.5, Тяжелое=2.0.
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        accident = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.carrier_fault and s.accident_severity and s.accident_severity != 'Нет':
                severity = ACCIDENT_SEVERITY_COEFFICIENTS.get(s.accident_severity, 1.0)
                accident += w * severity
        return round(accident / total * 100, 2)

    def _tracking(self, delivered):
        """
        Назначение:
            Доля рейсов с GPS: has_gps == True.
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        gps = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.has_gps:
                gps += w
        return round(gps / total * 100, 2)

    def _pod(self, delivered):
        """
        Назначение:
            Доля рейсов с POD: has_pod == True.
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Процент от 0 до 100.
        """
        total = 0.0
        pod = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            if s.has_pod:
                pod += w
        return round(pod / total * 100, 2)

    def _feedback(self, delivered):
        """
        Назначение:
            Средневзвешенная оценка клиентов (1-5).
        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.
        Возвращает:
            float: Оценка от 1.0 до 5.0.
        """
        total = 0.0
        score = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            score += s.client_rating * w
        return round(score / total, 2)

    def _rpk(self, delivered):
        """
        Назначение:
            Средневзвешенная цена за километр.

        Параметры:
            delivered (list[Shipment]): Доставленные рейсы.

        Возвращает:
            float: Рублей за км.
        """
        total = 0.0
        price_sum = 0.0
        km_sum = 0.0
        for s in delivered:
            w = self._decay_weight(s.pickup_window_start)
            total += w
            price_sum += float(s.price) * w
            km_sum += float(s.distance_km) * w
        return round(price_sum / km_sum, 2)