"""
Описание: Модуль сервиса запуска расчета рейтинга перевозчиков.
Содержит класс RunService, реализующий выполнение многокритериальной
оценки методами TOPSIS и VIKOR с весами SWARA.
Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
import json
from datetime import datetime, timezone

import numpy as np
from app import db
from app.models import Scenario, ScenarioCriterion, Run, RunResult, Criterion
from app.services.algorithms.swara import SwaraService
from app.services.algorithms.criterion_calc import CriteriaCalculator
from app.services.algorithms.topsis import TopsisService
from app.services.algorithms.vikor import VikorService


class RunService:
    """
    Назначение:
        Сервис запуска расчета рейтинга перевозчиков методами TOPSIS или VIKOR, SWARA.
    Параметры:
        topsis (TopsisService): Экземпляр сервиса TOPSIS.
        vikor (VikorService): Экземпляр сервиса VIKOR.
    Возвращает:
        Run: Объект запуска с результатами.
    """
    VALID_METHODS = {'topsis', 'vikor'}

    def __init__(self):
        """
        Назначение:
            Инициализация сервиса.
        Параметры:
            Нет.
        Возвращает:
            None.
        """
        self.topsis = TopsisService()
        self.vikor = VikorService(v=0.5)

    def execute(self, scenario_id, user_id):
        """
        Назначение:
            Запуск расчета рейтинга по заданному сценарию.
        Параметры:
            scenario_id (int): Идентификатор сценария.
            user_id (int): Идентификатор пользователя.
        Возвращает:
            Run: Объект выполненного запуска.
        """
        scenario = Scenario.query.get_or_404(scenario_id)

        scenario.status = 'в обработке'
        db.session.commit()

        try:
            method = getattr(scenario, 'method', 'topsis')
            if method not in self.VALID_METHODS:
                raise ValueError(f"Unknown method: '{method}'. Allowed: {self.VALID_METHODS}")
            links = ScenarioCriterion.query.filter_by(
                scenario_id=scenario.id, is_enabled=True
            ).order_by(ScenarioCriterion.order_no.asc()).all()
            if not links:
                raise ValueError("Не выбрано ни одного критерия. Добавьте минимум 2 критерия в настройках сценария.")
            if len(links) < 2:
                raise ValueError(f"Выбран только {len(links)} критерий. Для расчёта необходимо минимум 2 критерия.")

            selected_criteria = [Criterion.query.get(link.criterion_id) for link in links]
            missing_criteria = [link.criterion_id for link, crit in zip(links, selected_criteria) if crit is None]
            if missing_criteria:
                raise ValueError(f"Criteria not found in DB: {missing_criteria}")

            selected_codes = [c.code for c in selected_criteria]
            kinds = [c.kind for c in selected_criteria]

            calculator = CriteriaCalculator()
            calculator.load_data()
            calculated_data = calculator.calculate_all()

            matrix_raw, carriers_list = [], []
            for carrier in calculator.carriers:
                if carrier.carrier_id not in calculated_data:
                    continue

                carrier_shipments = [
                    s for s in calculator.shipments
                    if s.carrier_id == carrier.carrier_id
                ]
                if len(carrier_shipments) == 0:
                    continue

                delivered = [s for s in carrier_shipments if s.status == 'Доставлено']
                if len(delivered) == 0:
                    continue

                criteria_raw = calculated_data[carrier.carrier_id]['criteria_raw']
                row_raw = [float(criteria_raw.get(code, 0.0) or 0.0) for code in selected_codes]
                matrix_raw.append(row_raw)
                carriers_list.append(carrier)

            if not matrix_raw:
                raise ValueError('Нет перевозчиков с доставленными рейсами.')

            matrix_raw = np.array(matrix_raw, dtype=float)

            config = scenario.get_swara_config()
            if not config:
                raise ValueError('Настройки SWARA не найдены.')
            if len(config.get('ranking', [])) < 2:
                raise ValueError('Выберите минимум 2 критерия и настройте их важность в SWARA.')

            swara_weights = SwaraService.compute(config['ranking'], config['s_values'])
            missing_weights = set(selected_codes) - set(swara_weights.keys())
            if missing_weights:
                raise ValueError(f"SWARA config missing weights for criteria: {missing_weights}")

            weights = [swara_weights.get(code, 0.0) for code in selected_codes]
            if sum(weights) < 1e-12:
                raise ValueError("Sum of weights is zero.")

            if method == 'vikor':
                scores, debug = self.vikor.compute(matrix_raw, kinds, weights)
                method_name = 'VIKOR'
                ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

            else:
                scores, debug = self.topsis.compute(matrix_raw, kinds, weights)
                method_name = 'TOPSIS'
                ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

            run = Run(
                scenario_id=scenario.id,
                initiated_by=user_id,
                status='done',
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                meta_json=json.dumps({
                    'criteria_codes': selected_codes,
                    'criteria_names': [c.name for c in selected_criteria],
                    'criteria_kinds': kinds,
                    'weights': weights,
                    'method': method_name,
                    'swara_config': config
                }, ensure_ascii=False)
            )
            db.session.add(run)
            db.session.flush()

            for rank, idx in enumerate(ranking, start=1):
                carrier = carriers_list[idx]
                if method == 'topsis':
                    details = {
                        'criteria_values_raw': calculated_data[carrier.carrier_id]['criteria_raw'],
                        'criteria_values_norm': debug[idx]['norm_values'],
                        'criteria_codes': selected_codes,
                        'distance_to_best': debug[idx]['distance_to_best'],
                        'distance_to_worst': debug[idx]['distance_to_worst']
                    }
                else:
                    details = {
                        'criteria_values_raw': calculated_data[carrier.carrier_id]['criteria_raw'],
                        'criteria_values_norm': debug['X_norm'][idx],
                        'criteria_codes': selected_codes,
                        'S_value': debug['S_values'][idx],
                        'R_value': debug['R_values'][idx],
                        'Q_value': scores[idx]
                    }
                db.session.add(RunResult(
                    run_id=run.id,
                    carrier_id=carrier.carrier_id,
                    rank=rank,
                    score=scores[idx],
                    details_json=json.dumps(details, ensure_ascii=False)
                ))

            scenario.status = 'расчёт выполнен'
            db.session.commit()

        except Exception:
            scenario.status = 'ошибка'
            db.session.commit()
            raise

        return run

    def list_runs(self, scenario_id: int) -> list:
        """
        Назначение:
            Список всех запусков для сценария.
        Параметры:
            scenario_id (int): ID сценария.
        Возвращает:
            list[Run]: Список запусков, отсортированный по убыванию ID.
        """
        return Run.query.filter_by(scenario_id=scenario_id).order_by(Run.id.desc()).all()

    def get_run_detail(self, run_id: int):
        """
        Назначение:
            Запуск и его результаты по ID.
        Параметры:
            run_id (int): ID запуска.
        Возвращает:
            tuple: (Run, list[RunResult]).
        """
        run = self.get_run(run_id)
        results = self.get_run_results(run_id)
        return run, results

    def latest_results(self, scenario_id: int):
        """
        Назначение:
            Получение последнего запуска и его результатов для сценария.
        Параметры:
            scenario_id (int): Идентификатор сценария.
        Возвращает:
            tuple: (Run, list[RunResult]).
        """
        run = Run.query.filter_by(scenario_id=scenario_id).order_by(Run.id.desc()).first()
        if not run:
            return None, []
        rows = RunResult.query.filter_by(run_id=run.id).order_by(RunResult.rank.asc()).all()
        return run, rows

    def get_run(self, run_id: int) -> Run:
        """
        Назначение:
            Находит запуск по ID.
        Параметры:
            run_id (int): ID запуска.
        Возвращает:
            Run: Объект запуска (метаданные, статус, даты).
        """
        return Run.query.get_or_404(run_id)

    def get_run_results(self, run_id: int) -> list:
        """
        Назначение:
            Находит отсортированный список мест перевозчиков для запуска.
        Параметры:
            run_id (int): ID запуска.
        Возвращает:
            list[RunResult]: Список результатов, отсортированный по занятому месту.
        """
        return RunResult.query.filter_by(run_id=run_id).order_by(RunResult.rank.asc()).all()