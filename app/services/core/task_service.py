"""
Сервис управления фоновыми задачами.
Файл: app/services/core/task_service.py
"""
import logging
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from celery.result import AsyncResult
from app.extensions import celery

logger = logging.getLogger(__name__)


class TaskService:

    # ==========================================================================
    # РАСЧЁТ РЕЙТИНГА
    # ==========================================================================

    def start_run(self, scenario_id: int, user_id: int) -> dict:
        """
        Назначение:
            Создаёт фоновую задачу расчёта рейтинга.
        Параметры:
            scenario_id (int): ID сценария.
            user_id (int): ID пользователя.
        Возвращает:
            dict: {'task_id': str, 'status': str}
        """
        from app.tasks import run_scenario_task
        task = run_scenario_task.delay(scenario_id, user_id)
        logger.info('Создана задача расчёта scenario_id=%s task_id=%s', scenario_id, task.id)
        return {'task_id': task.id, 'status': 'запущен'}

    # ==========================================================================
    # ИМПОРТ ФАЙЛА
    # ==========================================================================

    def start_import(self, file_storage, name: str, description: str = '', skip_preprocess: bool = False) -> dict:
        """
        Назначение:
            Сохраняет файл на диск и создаёт фоновую задачу импорта.
        Параметры:
            file_storage: Файл из запроса (werkzeug FileStorage).
            name (str): Название датасета.
            description (str): Описание.
            skip_preprocess (bool): Пропустить предобработку.
        Возвращает:
            dict: {'task_id': str, 'status': str}
        """
        from app.tasks import import_dataset_task

        file_path = self._save_file(file_storage)
        task = import_dataset_task.delay(
            file_path=file_path,
            name=name,
            description=description,
            skip_preprocess=skip_preprocess,
        )
        logger.info('Создана задача импорта file=%s task_id=%s', file_path, task.id)
        return {'task_id': task.id, 'status': 'запущен'}

    # ==========================================================================
    # СТАТУС ЗАДАЧИ
    # ==========================================================================

    def get_status(self, task_id: str) -> dict:
        """
        Назначение:
            Возвращает текущий статус задачи из Redis.
        Параметры:
            task_id (str): ID задачи Celery.
        Возвращает:
            dict: {'task_id', 'status', 'result', 'error'}
        """
        result = AsyncResult(task_id, app=celery)
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() and not result.failed() else None,
            'error': str(result.result) if result.failed() else None,
        }

    # ==========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==========================================================================

    def _save_file(self, file_storage) -> str:
        """Сохраняет файл на диск и возвращает путь."""
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        safe_name = secure_filename(file_storage.filename)
        saved_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        file_path = upload_folder / saved_filename
        file_storage.save(file_path)
        return str(file_path)