"""
Модуль импорта данных из Excel в базу данных.
Выполняет загрузку перевозчиков и рейсов после предобработки.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from app import db
from app.models import Dataset, Carrier, Shipment


class ExcelImporter:
    """
    Назначение:
        Импорт данных о перевозчиках и рейсах в базу данных.
    Параметры:
        Нет.
    Возвращает:
        Dataset: Созданный датасет.
    """

    def __init__(self):
        self.stats = {
            'carriers': 0,
            'carriers_updated': 0,
            'shipments': 0,
            'skipped_shipments': 0
        }
        self.valid_carrier_ids: set = set()

    def _safe_int(self, val: Any) -> Optional[int]:
        """
        Назначение:
            Безопасное преобразование в целое число.
        Параметры:
            val (Any): Значение ячейки.
        Возвращает:
            int или None.
        """
        if pd.isna(val) or val == '':
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def _safe_float(self, val: Any) -> Optional[float]:
        """
        Назначение:
            Безопасное преобразование в число с плавающей точкой.
        Параметры:
            val (Any): Значение ячейки.
        Возвращает:
            float или None.
        """
        if pd.isna(val) or val == '':
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _safe_datetime(self, val: Any) -> Optional[datetime]:
        """
        Назначение:
            Безопасное преобразование в дату/время.
        Параметры:
            val (Any): Значение ячейки.
        Возвращает:
            datetime или None.
        """
        if pd.isna(val) or val == '':
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, pd.Timestamp):
            return val.to_pydatetime()
        try:
            return pd.to_datetime(val).to_pydatetime()
        except Exception:
            return None

    def _safe_bool(self, val: Any) -> Optional[bool]:
        """
        Назначение:
            Безопасное преобразование в булево значение.
        Параметры:
            val (Any): Значение ячейки.
        Возвращает:
            bool или None.
        """
        if pd.isna(val) or val == '':
            return None
        val_str = str(val).strip()
        if val_str in ['Да', 'да']:
            return True
        if val_str in ['Нет', 'нет']:
            return False
        return None

    def _safe_str(self, val: Any) -> Optional[str]:
        """
        Назначение:
            Безопасное преобразование в строку.
        Параметры:
            val (Any): Значение ячейки.
        Возвращает:
            str или None.
        """
        if pd.isna(val) or val == '':
            return None
        return str(val).strip()

    def import_from_dataframes(
            self,
            df_carriers: pd.DataFrame,
            df_shipments: pd.DataFrame,
            file_name: str,
            name: str = 'Dataset',
            description: str = ''
    ) -> Dataset:
        """
        Назначение:
            Импорт данных из DataFrame в базу данных.
        Параметры:
            df_carriers (DataFrame): Данные перевозчиков.
            df_shipments (DataFrame): Данные рейсов.
            file_name (str): Имя исходного файла.
            name (str): Название датасета.
            description (str): Описание датасета.
        Возвращает:
            Dataset: Созданный датасет.
        """
        dataset = Dataset(
            name=name,
            file_name=file_name,
            description=description,
            records_count=0
        )
        db.session.add(dataset)
        db.session.flush()

        try:
            if not df_carriers.empty:
                self._import_carriers(df_carriers)
                db.session.flush()

            self.valid_carrier_ids = set()
            for _, row in df_carriers.iterrows():
                carrier_id = self._safe_int(row.get('ID перевозчика'))
                if carrier_id:
                    self.valid_carrier_ids.add(carrier_id)

            if not df_shipments.empty:
                self._import_shipments(df_shipments, dataset.id)

            dataset.records_count = (
                (self.stats['carriers'] - self.stats['carriers_updated'])
                + self.stats['shipments']
            )
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        return dataset

    def import_excel(self, file_path: str, name: str = 'Dataset', description: str = '') -> Dataset:
        """
        Назначение:
            Чтение Excel-файла и импорт данных.
        Параметры:
            file_path (str): Путь к файлу.
            name (str): Название датасета.
            description (str): Описание датасета.
        Возвращает:
            Dataset: Созданный датасет.
        """
        df_carriers = pd.read_excel(file_path, sheet_name=0)
        df_shipments = pd.read_excel(file_path, sheet_name=1)

        return self.import_from_dataframes(
            df_carriers=df_carriers,
            df_shipments=df_shipments,
            file_name=Path(file_path).name,
            name=name,
            description=description
        )

    def _import_carriers(self, df: pd.DataFrame) -> None:
        """
        Назначение:
            Импорт перевозчиков в таблицу carrier.
        Параметры:
            df (DataFrame): Данные перевозчиков.
        Возвращает:
            None.
        """
        for _, row in df.iterrows():
            carrier_id = self._safe_int(row.get('ID перевозчика'))
            if not carrier_id:
                continue

            name = self._safe_str(row.get('Название')) or ''
            fleet_type = self._safe_str(row.get('Тип автопарка'))
            region = self._safe_str(row.get('Регион'))

            existing = db.session.get(Carrier, carrier_id)
            if existing:
                existing.company_name = name
                existing.fleet_type = fleet_type
                existing.region = region
                self.stats['carriers_updated'] += 1
            else:
                db.session.add(Carrier(
                    carrier_id=carrier_id,
                    company_name=name,
                    fleet_type=fleet_type,
                    region=region
                ))

            self.stats['carriers'] += 1

    def _import_shipments(self, df: pd.DataFrame, dataset_id: int) -> None:
        """
        Назначение:
            Импорт рейсов в таблицу shipment.
        Параметры:
            df (DataFrame): Данные рейсов.
            dataset_id (int): ID датасета.
        Возвращает:
            None.
        """
        for _, row in df.iterrows():
            shipment_id = self._safe_int(row.get('ID рейса'))
            if not shipment_id:
                self.stats['skipped_shipments'] += 1
                continue

            carrier_id = self._safe_int(row.get('ID перевозчика'))
            if not carrier_id:
                self.stats['skipped_shipments'] += 1
                continue

            if carrier_id not in self.valid_carrier_ids:
                self.stats['skipped_shipments'] += 1
                continue

            existing = db.session.get(Shipment, shipment_id)
            if existing:
                self.stats['skipped_shipments'] += 1
                continue

            db.session.add(Shipment(
                shipment_id=shipment_id,
                dataset_id=dataset_id,
                carrier_id=carrier_id,
                pickup_window_start=self._safe_datetime(row.get('Начало погрузки')),
                delivery_window_end=self._safe_datetime(row.get('Планируемое время доставки')),
                actual_delivery_time=self._safe_datetime(row.get('Фактическое время доставки')),
                client_rating=self._safe_int(row.get('Оценка клиента')),
                price=self._safe_float(row.get('Цена')),
                distance_km=self._safe_float(row.get('Расстояние км')),
                status=self._safe_str(row.get('Статус рейса')),
                has_gps=self._safe_bool(row.get('Был GPS')),
                has_pod=self._safe_bool(row.get('Наличие POD')),
                accident_severity=self._safe_str(row.get('Тяжесть ДТП')),
                carrier_fault=self._safe_bool(row.get('Вина перевозчика в ДТП')),
                claim_type=self._safe_str(row.get('Тип претензии'))
            ))

            self.stats['shipments'] += 1