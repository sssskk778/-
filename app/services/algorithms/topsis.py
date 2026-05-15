"""
Модуль многокритериальной оценки методом TOPSIS.
Реализует расчет рейтинга с векторной нормализацией.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
import numpy as np
from typing import List, Tuple, Dict, Any


class TopsisService:
    """
    Назначение:
        Многокритериальная оценка альтернатив методом TOPSIS.
    Параметры:
        Нет.
    Возвращает:
        scores (list[float]): Оценки альтернатив (0-1, больше = лучше).
        debug (list[dict]): Детали расчета.
    """

    def compute(
        self,
        raw_matrix: np.ndarray,
        kinds: List[str],
        weights: List[float]
    ) -> Tuple[List[float], List[Dict[str, Any]]]:
        """
        Назначение:
            Расчет рейтинга методом TOPSIS.
        Параметры:
            raw_matrix (np.ndarray): Матрица критериев (альтернативы x критерии).
            kinds (list[str]): Типы критериев ('benefit' или 'cost').
            weights (list[float]): Веса критериев (сумма = 1).
        Возвращает:
            tuple: (оценки, детали расчета).
        """
        X = np.array(raw_matrix, dtype=float)
        weights_arr = np.array(weights, dtype=float)
        m, n = X.shape

        denom = np.sqrt((X ** 2).sum(axis=0))
        denom = np.where(denom == 0, 1, denom)
        X_norm = X / denom

        V = X_norm * weights_arr

        ideal_best = np.zeros(n)
        ideal_worst = np.zeros(n)

        for j in range(n):
            col = V[:, j]
            if kinds[j] == "benefit":
                ideal_best[j] = col.max()
                ideal_worst[j] = col.min()
            else:
                ideal_best[j] = col.min()
                ideal_worst[j] = col.max()

        d_pos = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
        d_neg = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))

        eps = 1e-12
        score = d_neg / (d_pos + d_neg + eps)

        debug = [
            {
                "distance_to_best": float(d_pos[i]),
                "distance_to_worst": float(d_neg[i]),
                "norm_values": X_norm[i].tolist(),
            }
            for i in range(m)
        ]

        return score.tolist(), debug