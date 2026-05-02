# tests/test_excel_preprocessor.py
"""
Тестирование предобработки Excel-файлов.
Проверяется валидация данных о перевозчиках и рейсах.
"""
import pandas as pd
from datetime import datetime, timedelta
from app.services.excel_preprocessor import ExcelPreprocessor


def test_preprocessor_carriers_valid():
    """Корректные перевозчики проходят валидацию"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [1, 'ООО Тест', 'самосвалы', 'Центральный'],
        [2, 'ИП Петров', 'бортовые', 'Южный'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 2
    assert preprocessor.stats['valid_carriers'] == 2


def test_preprocessor_carriers_empty_name():
    """Короткое имя отбрасывается"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [1, 'A', 'самосвалы', 'Центральный'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 0


def test_preprocessor_carriers_duplicate_id():
    """Дубликат ID отбрасывается"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [1, 'ООО Тест', 'самосвалы', 'Центральный'],
        [1, 'ООО Клон', 'бортовые', 'Южный'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 1


def test_preprocessor_carriers_invalid_fleet():
    """Неверный тип автопарка отбрасывается"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [1, 'ООО Тест', 'грузовики', 'Центральный'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 0


def test_preprocessor_carriers_invalid_region():
    """Неверный регион отбрасывается"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [1, 'ООО Тест', 'самосвалы', 'Москва'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 0


def test_preprocessor_carriers_negative_id():
    """Отрицательный ID отбрасывается"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [-1, 'ООО Тест', 'самосвалы', 'Центральный'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 0


def test_preprocessor_carriers_zero_id():
    """Нулевой ID отбрасывается"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [0, 'ООО Тест', 'самосвалы', 'Центральный'],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 0


def test_preprocessor_carriers_empty_fields():
    """Пустые поля — строка удаляется"""
    preprocessor = ExcelPreprocessor()
    df = pd.DataFrame([
        [1, '', '', ''],
    ], columns=['ID перевозчика', 'Название', 'Тип автопарка', 'Регион'])
    result = preprocessor._validate_carriers(df)
    assert len(result) == 0
    assert preprocessor.stats['empty_carriers'] == 1


def test_preprocessor_shipments_delivered():
    """Доставленный рейс проходит"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), now + timedelta(hours=5),
         5, 1000, 100, 'Доставлено', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 1


def test_preprocessor_shipments_cancelled():
    """Отмененный рейс с Нет для delivery проходит"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Отменено', 'Нет', 'Нет', 'Нет', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 1


def test_preprocessor_shipments_no_show():
    """Неявка с Нет для delivery проходит"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Не приехал', 'Нет', 'Нет', 'Нет', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 1


def test_preprocessor_shipments_invalid_status():
    """Неверный статус отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), now + timedelta(hours=5),
         5, 1000, 100, 'В пути', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_future_date():
    """Дата в будущем отбрасывается"""
    preprocessor = ExcelPreprocessor()
    future = datetime.now() + timedelta(days=10)
    df = pd.DataFrame([
        [1, 1, future, future + timedelta(hours=5), future + timedelta(hours=5),
         5, 1000, 100, 'Доставлено', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_missing_carrier():
    """Несуществующий перевозчик отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 999, now, now + timedelta(hours=5), now + timedelta(hours=5),
         5, 1000, 100, 'Доставлено', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_delivery_not_net_for_cancelled():
    """Отмененный рейс с датой доставки вместо Нет отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), now + timedelta(hours=5),
         'Нет', 1000, 100, 'Отменено', 'Нет', 'Нет', 'Нет', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_rating_not_net_for_cancelled():
    """Отмененный рейс с оценкой вместо Нет отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         5, 1000, 100, 'Отменено', 'Нет', 'Нет', 'Нет', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_gps_da_for_cancelled():
    """GPS=Да для Отменено отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Отменено', 'Да', 'Нет', 'Нет', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_pod_da_for_cancelled():
    """POD=Да для Отменено отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Отменено', 'Нет', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_accident_not_net_for_cancelled():
    """ДТП != Нет для Отменено отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Отменено', 'Нет', 'Легкое', 'Нет', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_fault_not_net_for_cancelled():
    """Вина != Нет для Отменено отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Отменено', 'Нет', 'Нет', 'Да', 'Нет', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_claim_not_net_for_cancelled():
    """Претензия != Нет для Отменено отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), 'Нет',
         'Нет', 1000, 100, 'Отменено', 'Нет', 'Нет', 'Нет', 'Повреждение', 'Нет'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_accident_severity():
    """Доставленный рейс с ДТП проходит"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), now + timedelta(hours=5),
         5, 1000, 100, 'Доставлено', 'Да', 'Среднее', 'Да', 'Повреждение', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 1


def test_preprocessor_shipments_negative_price():
    """Отрицательная цена отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), now + timedelta(hours=5),
         5, -100, 100, 'Доставлено', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_shipments_negative_distance():
    """Отрицательное расстояние отбрасывается"""
    preprocessor = ExcelPreprocessor()
    now = datetime.now() - timedelta(days=1)
    df = pd.DataFrame([
        [1, 1, now, now + timedelta(hours=5), now + timedelta(hours=5),
         5, 1000, -50, 'Доставлено', 'Да', 'Нет', 'Нет', 'Нет', 'Да'],
    ], columns=ExcelPreprocessor.SHIPMENTS_COLUMNS)
    result = preprocessor._validate_shipments(df, {1})
    assert len(result) == 0


def test_preprocessor_report():
    """Отчет содержит нужные ключи"""
    preprocessor = ExcelPreprocessor()
    report = preprocessor.get_report()
    assert 'stats' in report
    assert 'errors' in report
    assert 'total_errors' in report