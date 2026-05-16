"""
Фоновые задачи Celery.
Файл: app/tasks.py
"""
import logging
from pathlib import Path
from app.extensions import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='tasks.run_scenario')
def run_scenario_task(self, scenario_id: int, user_id: int):
    logger.info('Запуск расчёта сценария %s пользователем %s', scenario_id, user_id)
    try:
        from app.services.core.run_service import RunService
        run = RunService().execute(scenario_id, user_id)
        logger.info('Расчёт сценария %s завершён, run_id=%s', scenario_id, run.id)
        return {'run_id': run.id, 'status': run.status}
    except Exception:
        logger.exception('Ошибка расчёта сценария %s', scenario_id)
        raise


@celery.task(bind=True, name='tasks.import_dataset')
def import_dataset_task(self, file_path: str, name: str, description: str = '', skip_preprocess: bool = False):
    logger.info('Импорт файла %s', file_path)
    path = Path(file_path)

    try:
        from app.services.data.excel_preprocessor import ExcelPreprocessor
        from app.services.data.excel_importer import ExcelImporter
        from app import db

        importer = ExcelImporter()

        if skip_preprocess:
            dataset = importer.import_excel(
                file_path=file_path,
                name=name,
                description=description,
            )
            preprocess_report = None
        else:
            preprocessor = ExcelPreprocessor()
            cleaned_data = preprocessor.process(file_path)
            preprocess_report = preprocessor.get_report()

            if cleaned_data['carriers'].empty and cleaned_data['shipments'].empty:
                raise ValueError('Нет валидных данных для импорта после предобработки')

            dataset = importer.import_from_dataframes(
                df_carriers=cleaned_data['carriers'],
                df_shipments=cleaned_data['shipments'],
                file_name=path.name,
                name=name,
                description=description,
            )

        if path.exists():
            path.unlink()

        logger.info('Импорт завершён, dataset_id=%s', dataset.id)

        result = {
            'dataset_id': dataset.id,
            'skipped_shipments': importer.stats.get('skipped_shipments', 0),
        }
        if preprocess_report:
            from app.services.data.dataset_service import DatasetService
            result['preprocess'] = DatasetService().format_preprocess_report(preprocess_report)

        return result

    except Exception:
        from app import db
        db.session.rollback()
        if path.exists():
            path.unlink()
        logger.exception('Ошибка импорта файла %s', file_path)
        raise