"""
Модуль сервиса управления датасетами.
Содержит класс DatasetService для загрузки, получения и удаления датасетов.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
from datetime import datetime
from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Dataset, Carrier, Shipment
from app.services.excel_preprocessor import ExcelPreprocessor
from app.services.excel_importer import ExcelImporter


class DatasetService:

    ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

    def list_datasets(self):
        """
        Назначение:
            Список всех датасетов.
        Параметры:
            Нет.
        Возвращает:
            list[Dataset]: Список датасетов.
        """
        return Dataset.query.order_by(Dataset.id.desc()).all()

    def get_dataset(self, dataset_id):
        """
        Назначение:
            Получение датасета по ID.
        Параметры:
            dataset_id (int): ID датасета.
        Возвращает:
            Dataset или 404.
        """
        return Dataset.query.get_or_404(dataset_id)

    def get_carriers(self):
        """
        Назначение:
            Список всех перевозчиков.
        Параметры:
            Нет.
        Возвращает:
            list[Carrier]: Список перевозчиков.
        """
        return Carrier.query.order_by(Carrier.company_name.asc()).all()

    def get_shipments(self, carrier_id=None, dataset_id=None):
        """
        Назначение:
            Список рейсов с фильтрацией.
        Параметры:
            carrier_id (int): ID перевозчика.
            dataset_id (int): ID датасета.
        Возвращает:
            list[Shipment]: Список рейсов.
        """
        query = Shipment.query
        if carrier_id:
            query = query.filter_by(carrier_id=carrier_id)
        if dataset_id:
            query = query.filter_by(dataset_id=dataset_id)
        return query.all()

    def delete_dataset(self, dataset_id):
        """
        Назначение:
            Удаление датасета.
        Параметры:
            dataset_id (int): ID датасета.
        Возвращает:
            dict: Информация об удаленном датасете.
        """
        ds = Dataset.query.get_or_404(dataset_id)
        result = {"id": ds.id, "name": ds.name, "file_name": ds.file_name}
        db.session.delete(ds)
        db.session.commit()
        return result

    def import_excel(self, file_storage, name='Загруженный датасет',
                     description='', skip_preprocess: bool = False):
        """
        Назначение:
            Полный цикл загрузки Excel-файла — сохранение, предобработка, импорт.
        Параметры:
            file_storage: Файл из формы.
            name (str): Название датасета.
            description (str): Описание.
            skip_preprocess (bool): Пропустить предобработку.
        Возвращает:
            dict: {'dataset': Dataset, 'preprocess_report': dict}.
        """
        original_filename = file_storage.filename
        if not original_filename:
            raise ValueError("Файл не имеет имени")

        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Недопустимый формат файла: .{ext}. "
                f"Разрешены: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            raise RuntimeError("UPLOAD_FOLDER не настроен в конфигурации")

        uploads = Path(upload_folder)
        uploads.mkdir(parents=True, exist_ok=True)

        safe_name = secure_filename(original_filename)
        saved_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        file_path = uploads / saved_filename
        file_storage.save(file_path)

        preprocess_report = None
        cleaned_data = None

        try:
            if not skip_preprocess:
                preprocessor = ExcelPreprocessor()
                cleaned_data = preprocessor.process(str(file_path))
                preprocess_report = preprocessor.get_report()

                if cleaned_data['carriers'].empty and cleaned_data['shipments'].empty:
                    raise ValueError("Нет валидных данных для импорта после предобработки")

            importer = ExcelImporter()

            if skip_preprocess:
                dataset = importer.import_excel(
                    file_path=str(file_path),
                    name=name,
                    description=description
                )
            else:
                dataset = importer.import_from_dataframes(
                    df_carriers=cleaned_data['carriers'],
                    df_shipments=cleaned_data['shipments'],
                    file_name=saved_filename,
                    name=name,
                    description=description
                )

            return {
                'dataset': dataset,
                'preprocess_report': preprocess_report
            }

        except Exception as e:
            db.session.rollback()
            if file_path.exists():
                file_path.unlink()
            raise ValueError(f"Ошибка импорта: {str(e)}")
