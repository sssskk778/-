# test_criteria_detail.py
"""
Детальный тест расчета критериев для одного перевозчика
Показывает все формулы и промежуточные вычисления
"""
from app import create_app
from app.models import CarrierRecord, TripRecord, Dataset
from datetime import datetime
import numpy as np

app = create_app()


def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_criteria_calculation_detail():
    """Детальный расчет критериев для ТК "Быстрый путь" """

    with app.app_context():
        # Берем перевозчика
        carrier = CarrierRecord.query.filter_by(carrier_id=1001).first()
        if not carrier:
            print("Перевозчик не найден!")
            return

        # Берем все рейсы этого перевозчика из всех датасетов
        trips = TripRecord.query.filter_by(carrier_id=carrier.carrier_id).all()

        # Получаем веса датасетов
        datasets = Dataset.query.all()
        current_year = 2026

        dataset_weights = {}
        for ds in datasets:
            age = current_year - ds.created_at.year
            weight = 1 / (age + 1)
            dataset_weights[ds.id] = weight

        total_weight = sum(dataset_weights.values())
        for ds_id in dataset_weights:
            dataset_weights[ds_id] /= total_weight

        print_section(f"РАСЧЕТ КРИТЕРИЕВ ДЛЯ: {carrier.company_name} (ID: {carrier.carrier_id})")

        # Информация о перевозчике
        print(f"\n📋 ДАННЫЕ ПЕРЕВОЗЧИКА:")
        print(f"   Регистрация: {carrier.registration_date}")
        print(f"   Водителей: {carrier.drivers_count}")
        print(f"   ТС: {carrier.vehicles_count}")
        print(f"   GPS: {'да' if carrier.has_gps_monitoring else 'нет'}")
        print(f"   Страховка: {'да' if carrier.has_insurance else 'нет'}")
        print(f"   Банкротство: {'да' if carrier.has_bankruptcy else 'нет'}")
        print(f"   Репутация: {carrier.reputation_score}")
        print(f"   Налоговая нагрузка: {carrier.tax_burden}")

        # Информация о рейсах по датасетам
        print(f"\n📊 РЕЙСЫ ПО ДАТАСЕТАМ:")
        for ds in datasets:
            ds_trips = [t for t in trips if t.dataset_id == ds.id]
            print(f"\n   Датасет '{ds.name}' (вес: {dataset_weights[ds.id] * 100:.1f}%):")
            for t in ds_trips:
                print(f"     - Рейс {t.trip_id}: {t.trip_date}")
                print(f"       План погрузки: {t.loading_date_plan}")
                print(f"       Факт погрузки: {t.loading_date_fact}")
                print(f"       План доставки: {t.delivery_date_plan}")
                print(f"       Факт доставки: {t.delivery_date_fact}")
                print(f"       Статус: {t.trip_status}")
                print(f"       Цена: {t.price_rub}")
                print(f"       Повреждения: {'да' if t.has_cargo_damage else 'нет'}")
                print(f"       Претензия: {'да' if t.has_claim else 'нет'}")
                print(f"       Оценка: {t.review_stars}")
                print(f"       Моб.приложение: {'да' if t.used_mobile_app else 'нет'}")

        # РАСЧЕТ КРИТЕРИЕВ
        print_section("РАСЧЕТ КАЖДОГО КРИТЕРИЯ")

        total_trips = len(trips)
        completed = [t for t in trips if t.trip_status == 'завершен']
        completed_count = len(completed)
        cancelled = [t for t in trips if t.trip_status == 'отменен']
        cancelled_count = len(cancelled)

        print(f"\n📈 БАЗОВАЯ СТАТИСТИКА:")
        print(f"   Всего рейсов: {total_trips}")
        print(f"   Завершено: {completed_count}")
        print(f"   Отменено: {cancelled_count}")

        # 1. Пунктуальность погрузки
        print(f"\n1. ПУНКТУАЛЬНОСТЬ ПРИБЫТИЯ ПОД ПОГРУЗКУ (loading_punctuality)")
        on_time_loading = 0
        for t in completed:
            if t.loading_date_plan and t.loading_date_fact:
                delta = (t.loading_date_fact - t.loading_date_plan).total_seconds() / 60
                if delta <= 0:
                    on_time_loading += 1
                    print(f"   Рейс {t.trip_id}: вовремя (опоздание {delta:.0f} мин) ✅")
                else:
                    print(f"   Рейс {t.trip_id}: опоздание на {delta:.0f} мин ❌")
        result = round(on_time_loading / completed_count * 100, 1) if completed_count > 0 else 0
        print(f"\n   Формула: {on_time_loading} / {completed_count} × 100 = {result}%")

        # 2. Своевременность доставки
        print(f"\n2. СВОЕВРЕМЕННОСТЬ ДОСТАВКИ (delivery_punctuality)")
        on_time_delivery = 0
        for t in completed:
            if t.delivery_date_plan and t.delivery_date_fact:
                delta = (t.delivery_date_fact - t.delivery_date_plan).total_seconds() / 60
                if delta <= 0:
                    on_time_delivery += 1
                    print(f"   Рейс {t.trip_id}: вовремя ✅")
                else:
                    print(f"   Рейс {t.trip_id}: опоздание на {delta:.0f} мин ❌")
        result = round(on_time_delivery / completed_count * 100, 1) if completed_count > 0 else 0
        print(f"\n   Формула: {on_time_delivery} / {completed_count} × 100 = {result}%")

        # 3. Сохранность груза
        print(f"\n3. СОХРАННОСТЬ ГРУЗА (cargo_safety)")
        no_damage = 0
        for t in completed:
            if not t.has_cargo_damage:
                no_damage += 1
                print(f"   Рейс {t.trip_id}: без повреждений ✅")
            else:
                print(f"   Рейс {t.trip_id}: повреждения ❌")
        result = round(no_damage / completed_count * 100, 1) if completed_count > 0 else 0
        print(f"\n   Формула: {no_damage} / {completed_count} × 100 = {result}%")

        # 4. Отказы
        print(f"\n4. ОТКАЗЫ ПОСЛЕ ПОДТВЕРЖДЕНИЯ (cancellation_rate)")
        for t in cancelled:
            print(f"   Рейс {t.trip_id}: отменен - {t.cancellation_reason}")
        result = round(cancelled_count / total_trips * 100, 1) if total_trips > 0 else 0
        print(f"\n   Формула: {cancelled_count} / {total_trips} × 100 = {result}%")

        # 5. Переносы дат
        print(f"\n5. ПЕРЕНОСЫ ДАТ (date_shifts)")
        late = 0
        for t in completed:
            if t.delivery_date_plan and t.delivery_date_fact:
                if t.delivery_date_fact > t.delivery_date_plan:
                    late += 1
                    print(f"   Рейс {t.trip_id}: опоздание с доставкой ❌")
                else:
                    print(f"   Рейс {t.trip_id}: доставка вовремя ✅")
        result = round(late / completed_count * 100, 1) if completed_count > 0 else 0
        print(f"\n   Формула: {late} / {completed_count} × 100 = {result}%")

        # 6. Доля выполненных
        print(f"\n6. ДОЛЯ ВЫПОЛНЕННЫХ РЕЙСОВ (completion_rate)")
        result = round(completed_count / total_trips * 100, 1) if total_trips > 0 else 0
        print(f"\n   Формула: {completed_count} / {total_trips} × 100 = {result}%")

        # 7. Скорость реакции
        print(f"\n7. СКОРОСТЬ РЕАКЦИИ НА ЗАЯВКУ (response_speed)")
        response_hours = []
        for t in completed:
            if t.response_date and t.loading_date_fact:
                delta = (t.loading_date_fact - t.response_date).total_seconds() / 3600
                response_hours.append(delta)
                print(f"   Рейс {t.trip_id}: отклик→погрузка = {delta:.1f} часов")
        result = round(sum(response_hours) / len(response_hours), 1) if response_hours else 24
        print(f"\n   Формула: сумма({response_hours}) / {len(response_hours)} = {result} часов")

        # 11. Уровень тарифов
        print(f"\n11. УРОВЕНЬ ТАРИФОВ (price_level)")
        prices = [float(t.price_rub) for t in completed if t.price_rub]
        for t in completed:
            if t.price_rub:
                print(f"   Рейс {t.trip_id}: {t.price_rub} ₽")
        result = round(sum(prices) / len(prices), 0) if prices else 50000
        print(f"\n   Формула: сумма({prices}) / {len(prices)} = {result} ₽")

        # 13. Срок деятельности
        print(f"\n13. СРОК ДЕЯТЕЛЬНОСТИ КОМПАНИИ (company_age)")
        if carrier.registration_date:
            years = datetime.now().year - carrier.registration_date.year
            print(f"   Регистрация: {carrier.registration_date}")
            print(f"   Текущий год: {datetime.now().year}")
            print(f"   Формула: {datetime.now().year} - {carrier.registration_date.year} = {years} лет")
        else:
            years = 1
            print(f"   Нет данных, по умолчанию = 1 год")

        # 14. Соотношение водителей и ТС
        print(f"\n14. СООТНОШЕНИЕ ВОДИТЕЛЕЙ И ТС (driver_vehicle_ratio)")
        if carrier.drivers_count and carrier.vehicles_count and carrier.vehicles_count > 0:
            ratio = round(carrier.drivers_count / carrier.vehicles_count, 2)
            print(f"   Водителей: {carrier.drivers_count}")
            print(f"   ТС: {carrier.vehicles_count}")
            print(f"   Формула: {carrier.drivers_count} / {carrier.vehicles_count} = {ratio}")
        else:
            ratio = 1.0
            print(f"   Недостаточно данных, по умолчанию = 1.0")

        # 15. Налоговая нагрузка
        print(f"\n15. НАЛОГОВАЯ НАГРУЗКА (tax_burden)")
        if carrier.tax_burden:
            result = round(carrier.tax_burden * 100, 1)
            print(f"   Налоговая нагрузка: {carrier.tax_burden}")
            print(f"   Формула: {carrier.tax_burden} × 100 = {result}%")
        else:
            result = 20
            print(f"   Нет данных, по умолчанию = {result}%")

        # 16. Объем перевозок
        print(f"\n16. ОБЪЕМ ПЕРЕВОЗОК (transport_volume)")
        print(f"   Всего рейсов: {total_trips}")

        # 17. Размер автопарка
        print(f"\n17. РАЗМЕР АВТОПАРКА (fleet_size)")
        print(f"   Количество ТС: {carrier.vehicles_count if carrier.vehicles_count else 1}")

        # 18. Уникальные клиенты
        print(f"\n18. УНИКАЛЬНЫЕ КЛИЕНТЫ (unique_clients)")
        clients = set(t.client_id for t in trips if t.client_id)
        print(f"   ID клиентов: {clients}")
        print(f"   Уникальных: {len(clients)}")

        # 20. Отзывы
        print(f"\n20. ОТЗЫВЫ (review_score)")
        reviews = [t.review_stars for t in trips if t.review_stars and t.review_stars > 0]
        for t in trips:
            if t.review_stars:
                print(f"   Рейс {t.trip_id}: {t.review_stars} ⭐ - {t.review_text}")
        result = round(sum(reviews) / len(reviews), 1) if reviews else 3
        print(f"\n   Формула: сумма({reviews}) / {len(reviews)} = {result} ⭐")

        # 21. Претензии
        print(f"\n21. ПРЕТЕНЗИИ (claims_rate)")
        claims = sum(1 for t in completed if t.has_claim)
        for t in completed:
            if t.has_claim:
                print(f"   Рейс {t.trip_id}: есть претензия ❌")
            else:
                print(f"   Рейс {t.trip_id}: нет претензии ✅")
        result = round(claims / completed_count * 100, 1) if completed_count > 0 else 0
        print(f"\n   Формула: {claims} / {completed_count} × 100 = {result}%")

        # ИТОГОВАЯ ТАБЛИЦА
        print_section("ИТОГОВЫЕ ЗНАЧЕНИЯ КРИТЕРИЕВ")

        criteria_values = {
            'loading_punctuality': round(on_time_loading / completed_count * 100, 1) if completed_count > 0 else 0,
            'delivery_punctuality': round(on_time_delivery / completed_count * 100, 1) if completed_count > 0 else 0,
            'cargo_safety': round(no_damage / completed_count * 100, 1) if completed_count > 0 else 0,
            'cancellation_rate': round(cancelled_count / total_trips * 100, 1) if total_trips > 0 else 0,
            'completion_rate': round(completed_count / total_trips * 100, 1) if total_trips > 0 else 0,
            'price_level': round(sum(prices) / len(prices), 0) if prices else 50000,
            'company_age': years,
            'driver_vehicle_ratio': ratio,
            'tax_burden': result,
            'transport_volume': total_trips,
            'fleet_size': carrier.vehicles_count if carrier.vehicles_count else 1,
            'unique_clients': len(clients),
            'review_score': round(sum(reviews) / len(reviews), 1) if reviews else 3,
            'claims_rate': round(claims / completed_count * 100, 1) if completed_count > 0 else 0,
            'reputation': carrier.reputation_score if carrier.reputation_score else 50,
            'gps_monitoring': 100 if carrier.has_gps_monitoring else 0,
            'insurance': 100 if carrier.has_insurance else 0,
            'no_bankruptcy': 0 if carrier.has_bankruptcy else 100,
        }

        print("\n┌─────────────────────────────────────┬────────────┐")
        print("│ Критерий                            │ Значение   │")
        print("├─────────────────────────────────────┼────────────┤")
        for name, value in criteria_values.items():
            print(f"│ {name:<35} │ {str(value):>10} │")
        print("└─────────────────────────────────────┴────────────┘")

        return criteria_values


def test_all_carriers():
    """Показывает критерии для всех перевозчиков в таблице"""

    with app.app_context():
        carriers = CarrierRecord.query.all()

        print_section("СРАВНИТЕЛЬНАЯ ТАБЛИЦА КРИТЕРИЕВ ПО ВСЕМ ПЕРЕВОЗЧИКАМ")

        # Заголовки
        print("\n┌────┬────────────────────────┬──────────┬──────────┬──────────┬──────────┬────────┐")
        print("│ №  │ Перевозчик              │ Пункт-ть │ Доставка │ Сохран-ть│ Отзывы   │ Рейсов │")
        print("├────┼────────────────────────┼──────────┼──────────┼──────────┼──────────┼────────┤")

        for i, carrier in enumerate(carriers, 1):
            trips = TripRecord.query.filter_by(carrier_id=carrier.carrier_id).all()
            completed = [t for t in trips if t.trip_status == 'завершен']
            completed_count = len(completed)

            # Быстрый расчет основных критериев
            on_time_loading = sum(1 for t in completed
                                  if t.loading_date_plan and t.loading_date_fact
                                  and t.loading_date_fact <= t.loading_date_plan)
            on_time_delivery = sum(1 for t in completed
                                   if t.delivery_date_plan and t.delivery_date_fact
                                   and t.delivery_date_fact <= t.delivery_date_plan)
            no_damage = sum(1 for t in completed if not t.has_cargo_damage)
            reviews = [t.review_stars for t in trips if t.review_stars and t.review_stars > 0]
            avg_review = round(sum(reviews) / len(reviews), 1) if reviews else 0

            punct = round(on_time_loading / completed_count * 100, 1) if completed_count > 0 else 0
            delivery = round(on_time_delivery / completed_count * 100, 1) if completed_count > 0 else 0
            safety = round(no_damage / completed_count * 100, 1) if completed_count > 0 else 0

            print(
                f"│ {i:<2} │ {carrier.company_name[:22]:<22} │ {punct:>6}% │ {delivery:>6}% │ {safety:>6}% │ {avg_review:>6}⭐ │ {len(trips):>6} │")

        print("└────┴────────────────────────┴──────────┴──────────┴──────────┴──────────┴────────┘")


if __name__ == '__main__':
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 20 + "ДЕТАЛЬНЫЙ ТЕСТ РАСЧЕТА КРИТЕРИЕВ" + " " * 20 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)

    # Детальный расчет для одного перевозчика
    test_criteria_calculation_detail()

    # Сравнительная таблица по всем
    test_all_carriers()

    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 25 + "ТЕСТ ЗАВЕРШЕН" + " " * 25 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)