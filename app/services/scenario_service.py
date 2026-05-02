"""
Модуль сервиса управления сценариями оценки.
Содержит класс ScenarioService для создания, редактирования и удаления сценариев.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
from app import db
from app.models import Scenario, ScenarioCriterion, Criterion

class ScenarioService:
    """
    Назначение:
        Сервис для создания, редактирования, удаления и получения сценариев.
    Параметры:
        Нет.
    Возвращает:
        Scenario: Объект сценария.
    """

    VALID_METHODS = {'topsis', 'vikor'}

    def list_all(self):
        """
        Назначение:
            Получить список всех сценариев.
        Параметры:
            Нет.
        Возвращает:
            list[Scenario]: Список сценариев.
        """
        return Scenario.query.order_by(Scenario.id.asc()).all()

    def get(self, scenario_id):
        """
        Назначение:
            Найти сценарий по ID.
        Параметры:
            scenario_id (int): ID сценария.
        Возвращает:
            Scenario: Объект сценария или 404.
        """
        return Scenario.query.get_or_404(scenario_id)

    def create(self, payload, user_id):
        """
        Назначение:
            Создать новый сценарий с привязкой критериев.
        Параметры:
            payload (dict): Данные сценария (name, description, method, criterion_ids).
            user_id (int): ID пользователя-создателя.
        Возвращает:
            Scenario: Созданный сценарий.
        """
        name = (payload.get('name') or '').strip()
        if not name:
            raise ValueError("Scenario name is required")

        method = payload.get('method', 'topsis')
        if method not in self.VALID_METHODS:
            raise ValueError(f"Unknown method: '{method}'. Allowed: {self.VALID_METHODS}")

        scenario = Scenario(
            name=name,
            description=(payload.get('description') or '').strip(),
            method=method,
            status='черновик',
            created_by=user_id,
        )
        db.session.add(scenario)
        db.session.flush()

        self._sync_criteria(scenario.id, payload.get('criterion_ids', []))
        db.session.commit()
        return scenario

    def update(self, scenario_id, payload):
        """
        Назначение:
            Обновить существующий сценарий и его критерии.
        Параметры:
            scenario_id (int): ID сценария.
            payload (dict): Новые данные.
        Возвращает:
            Scenario: Обновленный сценарий.
        """
        scenario = Scenario.query.get_or_404(scenario_id)

        name = (payload.get('name') or '').strip()
        if not name:
            raise ValueError("Scenario name is required")

        method = payload.get('method', 'topsis')
        if method not in self.VALID_METHODS:
            raise ValueError(f"Unknown method: '{method}'. Allowed: {self.VALID_METHODS}")

        scenario.name = name
        scenario.description = (payload.get('description') or '').strip()
        scenario.method = method

        ScenarioCriterion.query.filter_by(scenario_id=scenario.id).delete()
        self._sync_criteria(scenario.id, payload.get('criterion_ids', []))

        db.session.commit()
        return scenario

    def delete(self, scenario_id):
        """
        Назначение:
            Удалить сценарий и все связанные данные (каскадно).
        Параметры:
            scenario_id (int): ID сценария.
        Возвращает:
            None.
        """
        scenario = Scenario.query.get_or_404(scenario_id)
        db.session.delete(scenario)
        db.session.commit()

    def _sync_criteria(self, scenario_id, criterion_ids):
        """
        Назначение:
            Привязать критерии к сценарию.
        Параметры:
            scenario_id (int): ID сценария.
            criterion_ids (list[int]): Список ID критериев.
        Возвращает:
            None.
        """
        if not criterion_ids:
            return

        existing = Criterion.query.filter(Criterion.id.in_(criterion_ids)).all()
        existing_ids = {c.id for c in existing}
        missing = set(criterion_ids) - existing_ids

        if missing:
            raise ValueError(f"Criteria not found: {sorted(missing)}")

        for idx, cid in enumerate(criterion_ids, start=1):
            db.session.add(ScenarioCriterion(
                scenario_id=scenario_id,
                criterion_id=cid,
                is_enabled=True,
                order_no=idx
            ))