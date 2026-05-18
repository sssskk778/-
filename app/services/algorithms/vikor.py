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
        scores (list[float]): Оценки альтернатив (0-1, больше = лучше).
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

        # Шаг 1. Определение идеального f+ и анти-идеального f- по исходной матрице X
        f_best = np.zeros(n)
        f_worst = np.zeros(n)
        for j in range(n):
            col = X[:, j]
            if kinds[j] == 'benefit':
                f_best[j] = col.max()
                f_worst[j] = col.min()
            else:
                f_best[j] = col.min()
                f_worst[j] = col.max()

        # Шаг 2. Линейная нормализация — нормализованное отклонение от идеала
        # d_ij = (f_j+ - x_ij) / (f_j+ - f_j-)
        D = np.zeros_like(X)
        for j in range(n):
            denom = f_best[j] - f_worst[j]
            if abs(denom) < 1e-12:
                D[:, j] = 0.0
            else:
                D[:, j] = (f_best[j] - X[:, j]) / denom

        # Шаг 3. Суммарное взвешенное отклонение S и максимальное отклонение R
        S = np.zeros(m)
        R = np.zeros(m)
        for i in range(m):
            for j in range(n):
                weighted = weights_arr[j] * D[i, j]
                S[i] += weighted
                R[i] = max(R[i], weighted)

        # Шаг 4. Компромиссный индекс Q
        S_min, S_max = S.min(), S.max()
        R_min, R_max = R.min(), R.max()
        Q = np.zeros(m)
        for i in range(m):
            s_part = 0.0 if abs(S_max - S_min) < 1e-12 else (S[i] - S_min) / (S_max - S_min)
            r_part = 0.0 if abs(R_max - R_min) < 1e-12 else (R[i] - R_min) / (R_max - R_min)
            Q[i] = self.v * s_part + (1 - self.v) * r_part

        # Шаг 5. Инверсия Q для унификации с TOPSIS (1 = лучший перевозчик)
        Q_min, Q_max = Q.min(), Q.max()
        if abs(Q_max - Q_min) < 1e-12:
            scores = np.ones(m)
        else:
            scores = 1.0 - (Q - Q_min) / (Q_max - Q_min)

        debug = {
            "f_best": f_best.tolist(),
            "f_worst": f_worst.tolist(),
            "D_values": D.tolist(),
            "X_norm": D.tolist(),
            "S_values": S.tolist(),
            "R_values": R.tolist(),
            "Q_values": Q.tolist(),
            "scores": scores.tolist(),
        }

        print("f_best:", f_best.tolist())
        print("f_worst:", f_worst.tolist())
        print("D:", D.tolist())
        print("S:", S.tolist())
        print("Q:", Q.tolist())
        print("scores:", scores.tolist())
        return scores.tolist(), debug