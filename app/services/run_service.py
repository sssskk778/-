# app/services/run_service.py
import json
from datetime import datetime
import numpy as np
from app import db
from app.models import Scenario, ScenarioCriterion, Run, RunResult, Criterion, Carrier
from app.services.swara import SwaraService
from app.services.criterion_calc import CriteriaCalculator
from app.services.topsis import TopsisService
from app.services.vikor import VikorService


class RunService:
    def __init__(self):
        self.topsis = TopsisService()
        self.vikor = VikorService(v=0.5)

    def execute(self, scenario_id, user_id):
        scenario = Scenario.query.get_or_404(scenario_id)

        links = ScenarioCriterion.query.filter_by(
            scenario_id=scenario.id,
            is_enabled=True
        ).order_by(ScenarioCriterion.order_no.asc()).all()

        selected_criteria = [Criterion.query.get(link.criterion_id) for link in links]
        selected_codes = [c.code for c in selected_criteria]
        kinds = [c.kind for c in selected_criteria]

        method = getattr(scenario, 'method', 'topsis')

        # =========================================================================
        # 1. РАСЧЁТ СЫРЫХ КРИТЕРИЕВ
        # =========================================================================
        calculator = CriteriaCalculator()
        calculator.load_data()
        calculated_data = calculator.calculate_all()

        # =========================================================================
        # 2. ФОРМИРОВАНИЕ СЫРОЙ МАТРИЦЫ
        # =========================================================================
        matrix_raw = []
        names = []
        carriers_list = []

        for carrier in calculator.carriers:
            if carrier.carrier_id in calculated_data:
                criteria_raw = calculated_data[carrier.carrier_id]['criteria_raw']
                row_raw = [float(criteria_raw.get(code, 0.0) or 0.0) for code in selected_codes]
                matrix_raw.append(row_raw)
                names.append(carrier.name)
                carriers_list.append(carrier)

        if not matrix_raw:
            raise ValueError('Нет данных для расчета')

        matrix_raw = np.array(matrix_raw, dtype=float)

        print("\n" + "=" * 100)
        print("СЫРАЯ МАТРИЦА КРИТЕРИЕВ")
        print("=" * 100)
        print(f"{'Перевозчик':<25}", end="")
        for code in selected_codes:
            print(f"{code[:12]:>12}", end="")
        print()
        print("-" * 100)
        for i, name in enumerate(names):
            print(f"{name:<25}", end="")
            for j in range(len(selected_codes)):
                print(f"{matrix_raw[i, j]:>12.2f}", end="")
            print()

        # =========================================================================
        # 3. ВЕСА МЕТОДОМ SWARA (без дополнительной нормализации)
        # =========================================================================
        config = scenario.get_swara_config()
        if not config:
            raise ValueError('Настройки SWARA не найдены')

        swara_weights = SwaraService.compute(config['ranking'], config['s_values'])
        weights = [swara_weights.get(code, 0.0) for code in selected_codes]

        print("\n" + "=" * 100)
        print("ВЕСА КРИТЕРИЕВ (SWARA)")
        print("=" * 100)
        for code, weight in zip(selected_codes, weights):
            print(f"  {code:<25}: {weight:.4f}")

        # =========================================================================
        # 4. ВЫБОР МЕТОДА И РАСЧЁТ
        # =========================================================================
        if method == 'vikor':
            scores, debug = self.vikor.compute(matrix_raw, kinds, weights)
            method_name = 'VIKOR + SWARA'
            # VIKOR: Q_raw меньше = лучше, сортируем по возрастанию scores (Q_raw)
            ranking = sorted(range(len(scores)), key=lambda i: scores[i])
        else:
            scores, debug = self.topsis.compute(matrix_raw, kinds, weights)
            method_name = 'TOPSIS + SWARA'
            # TOPSIS: Score больше = лучше, сортируем по убыванию
            ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        # =========================================================================
        # 5. ВЫВОД РЕЗУЛЬТАТОВ
        # =========================================================================
        print("\n" + "=" * 100)
        print(f"ИТОГОВЫЕ РЕЗУЛЬТАТЫ ({method_name})")
        print("=" * 100)

        if method == 'topsis':
            print(f"{'Место':<6} {'Перевозчик':<25} {'Score':>10} {'d+':>10} {'d-':>10}")
            print("-" * 60)
            for rank, idx in enumerate(ranking, start=1):
                d_pos = debug[idx]['distance_to_best']
                d_neg = debug[idx]['distance_to_worst']
                print(f"{rank:<6} {names[idx]:<25} {scores[idx]:>10.4f} {d_pos:>10.4f} {d_neg:>10.4f}")
        else:
            print(f"{'Место':<6} {'Перевозчик':<25} {'Q':>10} {'S':>10} {'R':>10}")
            print("-" * 60)
            for rank, idx in enumerate(ranking, start=1):
                print(f"{rank:<6} {names[idx]:<25} {scores[idx]:>10.4f} "
                      f"{debug['S_values'][idx]:>10.4f} {debug['R_values'][idx]:>10.4f}")

        # =========================================================================
        # 6. СОХРАНЕНИЕ
        # =========================================================================
        run = Run(
            scenario_id=scenario.id,
            initiated_by=user_id,
            status='done',
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            meta_json=json.dumps({
                'criteria_codes': selected_codes,
                'criteria_names': [c.name for c in selected_criteria],
                'criteria_kinds': kinds,
                'weights': weights,
                'method': method_name,
                'weight_mode': 'swara',
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
                    'criteria_codes': selected_codes,
                    'distance_to_best': debug[idx]['distance_to_best'],
                    'distance_to_worst': debug[idx]['distance_to_worst']
                }
            else:
                details = {
                    'criteria_values_raw': calculated_data[carrier.carrier_id]['criteria_raw'],
                    'criteria_codes': selected_codes,
                    'S_value': debug['S_values'][idx],
                    'R_value': debug['R_values'][idx],
                    'Q_value': scores[idx]
                }

            db.session.add(RunResult(
                run_id=run.id,
                carrier_id=carrier.carrier_id,
                company_name=names[idx],
                rank=rank,
                score=float(scores[idx]),
                details_json=json.dumps(details, ensure_ascii=False)
            ))

        scenario.status = 'расчёт выполнен'
        db.session.commit()

        return run

    def latest_results(self, scenario_id):
        run = Run.query.filter_by(scenario_id=scenario_id).order_by(Run.id.desc()).first()
        if not run:
            return None, []
        rows = RunResult.query.filter_by(run_id=run.id).order_by(RunResult.rank.asc()).all()
        return run, rows

    def get_run(self, run_id):
        return Run.query.get_or_404(run_id)

    def get_run_results(self, run_id):
        return RunResult.query.filter_by(run_id=run_id).order_by(RunResult.rank.asc()).all()

    def delete_run(self, run_id):
        run = Run.query.get_or_404(run_id)
        RunResult.query.filter_by(run_id=run_id).delete()
        db.session.delete(run)
        db.session.commit()
        return True

