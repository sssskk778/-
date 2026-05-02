"""
Модуль многокритериальной оценки методом VIKOR.
Реализует расчет рейтинга с линейной нормализацией.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
import numpy as np
from typing import List, Tuple, Dict, Any

class VikorService:
    """
    Назначение:
        Многокритериальная оценка альтернатив методом VIKOR.
    Параметры:
        v (float): Коэффициент компромисса (0 — минимум R, 1 — минимум S).
                   По умолчанию 0.5.
    Возвращает:
        scores (list[float]): Оценки альтернатив (0-1, меньше = лучше).
        debug (dict): Детали расчета для сохранения в БД.
    """

    def __init__(self, v: float = 0.5):
        """
        Назначение:
            Инициализация сервиса VIKOR.
        Параметры:
            v (float): Коэффициент компромисса.
        Возвращает:
            None.
        """
        self.v = v

    def compute(
        self,
        raw_matrix: np.ndarray,
        kinds: List[str],
        weights: List[float]
    ) -> Tuple[List[float], Dict[str, Any]]:
        """
        Назначение:
            Расчет рейтинга методом VIKOR.
        Параметры:
            raw_matrix (np.ndarray): Матрица критериев (альтернативы x критерии).
            kinds (list[str]): Типы критериев ('benefit' или 'cost').
            weights (list[float]): Веса критериев.
        Возвращает:
            tuple: (оценки, детали расчета).
        """
        X = np.array(raw_matrix, dtype=float)
        weights_arr = np.array(weights, dtype=float)
        m, n = X.shape

        X_norm = np.zeros_like(X)
        for j in range(n):
            col = X[:, j]
            min_val = col.min()
            max_val = col.max()
            if max_val - min_val < 1e-12:
                X_norm[:, j] = 0.5
            elif kinds[j] == "benefit":
                X_norm[:, j] = (col - min_val) / (max_val - min_val)
            else:
                X_norm[:, j] = (max_val - col) / (max_val - min_val)

        f_best = X_norm.max(axis=0)
        f_worst = X_norm.min(axis=0)

        S = np.zeros(m)
        R = np.zeros(m)
        for i in range(m):
            for j in range(n):
                denom = f_best[j] - f_worst[j]
                diff = 0.0 if denom < 1e-12 else (f_best[j] - X_norm[i, j]) / denom
                weighted = weights_arr[j] * diff
                S[i] += weighted
                R[i] = max(R[i], weighted)

        S_min, S_max = S.min(), S.max()
        R_min, R_max = R.min(), R.max()
        Q = np.zeros(m)
        for i in range(m):
            s_part = 0.0 if abs(S_max - S_min) < 1e-12 else (S[i] - S_min) / (S_max - S_min)
            r_part = 0.0 if abs(R_max - R_min) < 1e-12 else (R[i] - R_min) / (R_max - R_min)
            Q[i] = self.v * s_part + (1 - self.v) * r_part

        Q_min, Q_max = Q.min(), Q.max()
        scores = np.zeros(m) if abs(Q_max - Q_min) < 1e-12 else (Q - Q_min) / (Q_max - Q_min)

        debug = {
            "X_norm": X_norm.tolist(),
            "S_values": S.tolist(),
            "R_values": R.tolist(),
            "Q_value": scores.tolist(),
        }

        return scores.tolist(), debug