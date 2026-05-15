"""
Модуль сервиса управления перевозчиками.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
from app.models import Carrier, Shipment


class CarrierService:

    def list_carriers(self) -> list:
        return Carrier.query.order_by(Carrier.company_name.asc()).all()

    def get_carrier_stats(self, carrier_id: int) -> dict:
        shipments = Shipment.query.filter_by(carrier_id=carrier_id).all()
        rated = [s.client_rating for s in shipments if s.client_rating is not None]
        return {
            'total_shipments': len(shipments),
            'delivered': sum(1 for s in shipments if s.status == 'Доставлено'),
            'cancelled': sum(1 for s in shipments if s.status == 'Отменено'),
            'no_show': sum(1 for s in shipments if s.status == 'Не приехал'),
            'avg_rating': round(sum(rated) / len(rated), 2) if rated else None,
            'total_price': sum(float(s.price) for s in shipments if s.price) or 0,
        }


    def get_dataset_counts(self, dataset_id: int) -> dict:
        return {
            'carriers_count': Carrier.query.count(),
            'shipments_count': Shipment.query.filter_by(dataset_id=dataset_id).count(),
        }