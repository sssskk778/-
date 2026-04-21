# app/services/dataset_service.py
from datetime import datetime
from pathlib import Path
from flask import current_app
from app import db
from app.models import (
    Dataset, Carrier, Shipment, ShipmentEvent,
    ShipmentDocument, Claim, CarrierBehavior
)
from app.services.csv_importer import CSVImporter
from app.services.preprocess_csv import CSVPreprocessor


class DatasetService:

    def list_datasets(self):
        return Dataset.query.order_by(Dataset.id.desc()).all()

    def get_dataset(self, dataset_id):
        return Dataset.query.get_or_404(dataset_id)

    def get_carriers(self, dataset_id=None):
        query = Carrier.query
        if dataset_id:
            query = query.filter_by(dataset_id=dataset_id)
        return query.order_by(Carrier.name.asc()).all()

    def get_shipments(self, carrier_id=None, dataset_id=None):
        query = Shipment.query
        if carrier_id:
            query = query.filter_by(carrier_id=carrier_id)
        if dataset_id:
            query = query.filter_by(dataset_id=dataset_id)
        return query.order_by(Shipment.created_at.desc()).all()

    def delete_dataset(self, dataset_id):
        ds = Dataset.query.get_or_404(dataset_id)
        Claim.query.filter(Claim.shipment_id.in_(
            db.session.query(Shipment.shipment_id).filter_by(dataset_id=dataset_id)
        )).delete(synchronize_session=False)
        ShipmentDocument.query.filter(ShipmentDocument.shipment_id.in_(
            db.session.query(Shipment.shipment_id).filter_by(dataset_id=dataset_id)
        )).delete(synchronize_session=False)
        ShipmentEvent.query.filter(ShipmentEvent.shipment_id.in_(
            db.session.query(Shipment.shipment_id).filter_by(dataset_id=dataset_id)
        )).delete(synchronize_session=False)
        Shipment.query.filter_by(dataset_id=dataset_id).delete()
        CarrierBehavior.query.filter(CarrierBehavior.carrier_id.in_(
            db.session.query(Carrier.carrier_id).filter_by(dataset_id=dataset_id)
        )).delete(synchronize_session=False)
        Carrier.query.filter_by(dataset_id=dataset_id).delete()
        db.session.delete(ds)
        db.session.commit()
        return True

    def import_csv(self, file_storage, name='Загруженный датасет', description=''):
        """
        Загрузка датасета из CSV-файла с предобработкой и импортом.
        """
        uploads = Path(current_app.config['UPLOAD_FOLDER'])
        uploads.mkdir(parents=True, exist_ok=True)

        # Сохраняем исходный файл
        safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_storage.filename}"
        raw_path = uploads / f"raw_{safe_filename}"
        file_storage.save(raw_path)

        try:
            # Шаг 1: Предобработка CSV (очистка и валидация)
            cleaned_content = CSVPreprocessor.process(str(raw_path))

            # Шаг 2: Сохраняем очищенный файл
            cleaned_path = uploads / f"cleaned_{safe_filename}"
            with open(cleaned_path, 'w', encoding='utf-8-sig') as f:
                f.write(cleaned_content)

            # Шаг 3: Импорт через CSVImporter
            importer = CSVImporter()
            dataset = importer.import_csv(
                file_path=str(cleaned_path),
                name=name,
                description=description
            )

            return dataset

        except Exception as e:
            raise Exception(f"Ошибка при импорте CSV: {str(e)}")