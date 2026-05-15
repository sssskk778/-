# tests/test_excel_importer.py
"""
Тестирование импорта данных в БД.
Проверяется создание перевозчиков и рейсов из DataFrame.
"""
import pandas as pd
import random
from app.services.data.excel_importer import ExcelImporter


def test_safe_int():
    importer = ExcelImporter()
    assert importer._safe_int(123) == 123
    assert importer._safe_int('456') == 456
    assert importer._safe_int('') is None
    assert importer._safe_int(None) is None


def test_safe_float():
    importer = ExcelImporter()
    assert importer._safe_float(100.5) == 100.5
    assert importer._safe_float('200.75') == 200.75
    assert importer._safe_float('') is None


def test_safe_bool():
    importer = ExcelImporter()
    assert importer._safe_bool('Да') == True
    assert importer._safe_bool('да') == True
    assert importer._safe_bool('Нет') == False
    assert importer._safe_bool('нет') == False
    assert importer._safe_bool('') is None


def test_import_carriers_from_dataframe(app):
    with app.app_context():
        importer = ExcelImporter()
        cid = random.randint(10000, 99999)
        df = pd.DataFrame([
            [cid, 'ООО Тест', 'самосвалы', 'Центральный'],
        ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
        importer._import_carriers(df)
        assert importer.stats['carriers'] == 1


def test_import_shipments_from_dataframe(app):
    with app.app_context():
        from app.models import Dataset, Carrier
        from app import db

        cid = random.randint(10000, 99999)
        c = Carrier(carrier_id=cid, company_name='Test')
        db.session.add(c)
        db.session.commit()

        ds = Dataset(name='Test', records_count=1)
        db.session.add(ds)
        db.session.flush()

        importer = ExcelImporter()
        importer.valid_carrier_ids = {cid}

        sid = random.randint(10000, 99999)
        df = pd.DataFrame([
            [sid, cid, '2026-01-01 08:00:00', '2026-01-01 18:00:00',
             '2026-01-01 18:00:00', 5, 1000, 100,
             'Доставлено', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
        ], columns=['ID рейса', 'ID перевозчика', 'Начало погрузки',
                    'Планируемое время доставки', 'Фактическое время доставки',
                    'Оценка клиента', 'Цена', 'Расстояние км',
                    'Статус рейса', 'Был GPS', 'Тяжесть ДТП',
                    'Вина перевозчика в ДТП', 'Тип претензии', 'Наличие POD'])
        importer._import_shipments(df, ds.id)
        assert importer.stats['shipments'] == 1
