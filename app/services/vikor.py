import numpy as np
from typing import List, Tuple, Dict, Any


class VikorService:
    """VIKOR метод многокритериального анализа (с линейной нормализацией)"""

    def __init__(self, v: float = 0.5):
        if not (0 <= v <= 1):
            raise ValueError("v must be in [0,1]")
        self.v = v

    def compute(
        self,
        raw_matrix: np.ndarray,
        kinds: List[str],   # "benefit" / "cost"
        weights: List[float]
    ) -> Tuple[List[float], Dict[str, Any]]:

        X = np.array(raw_matrix, dtype=float)
        m, n = X.shape

        if m == 0:
            raise ValueError("Empty matrix")

        weights = np.array(weights, dtype=float)

        # =========================================================================
        # 1. ЛИНЕЙНАЯ (MIN-MAX) НОРМАЛИЗАЦИЯ
        # Приводим ВСЕ критерии к виду: больше = лучше
        # =========================================================================
        X_norm = np.zeros_like(X)

        for j in range(n):
            col = X[:, j]
            min_val = col.min()
            max_val = col.max()

            if max_val - min_val < 1e-12:
                X_norm[:, j] = 0.5
            else:
                if kinds[j] == "benefit":
                    X_norm[:, j] = (col - min_val) / (max_val - min_val)
                else:  # cost → инверсия
                    X_norm[:, j] = (max_val - col) / (max_val - min_val)

        # =========================================================================
        # 2. Идеальные и анти-идеальные значения
        # ВАЖНО: после нормализации ВСЕ критерии = benefit
        # =========================================================================
        f_best = X_norm.max(axis=0)
        f_worst = X_norm.min(axis=0)

        # =========================================================================
        # 3. Расчёт S и R
        # =========================================================================
        S = np.zeros(m)
        R = np.zeros(m)

        for i in range(m):
            s_i = 0.0
            r_i = 0.0

            for j in range(n):
                denom = f_best[j] - f_worst[j]

                if denom < 1e-12:
                    diff = 0.0
                else:
                    diff = (f_best[j] - X_norm[i, j]) / denom

                weighted = weights[j] * diff
                s_i += weighted
                r_i = max(r_i, weighted)

            S[i] = s_i
            R[i] = r_i

        # =========================================================================
        # 4. Расчёт Q (меньше = лучше!)
        # =========================================================================
        S_min, S_max = S.min(), S.max()
        R_min, R_max = R.min(), R.max()

        Q = np.zeros(m)

        for i in range(m):
            s_part = 0.0 if abs(S_max - S_min) < 1e-12 else (S[i] - S_min) / (S_max - S_min)
            r_part = 0.0 if abs(R_max - R_min) < 1e-12 else (R[i] - R_min) / (R_max - R_min)

            Q[i] = self.v * s_part + (1 - self.v) * r_part

        # =========================================================================
        # 5. Нормализация Q (для UI)
        # 0 = лучший, 1 = худший
        # =========================================================================
        Q_min, Q_max = Q.min(), Q.max()

        if abs(Q_max - Q_min) < 1e-12:
            Q_norm = np.zeros(m)
        else:
            Q_norm = (Q - Q_min) / (Q_max - Q_min)

        # ❗ НЕ инвертируем (VIKOR: меньше = лучше)
        scores = Q_norm

        # =========================================================================
        # DEBUG (очень полезно для диплома)
        # =========================================================================
        debug = {
            "X_norm": X_norm.tolist(),
            "f_best": f_best.tolist(),
            "f_worst": f_worst.tolist(),
            "S_values": S.tolist(),
            "R_values": R.tolist(),
            "Q_raw": Q.tolist(),
            "Q_norm": Q_norm.tolist(),
            "note": "VIKOR: меньше значение score = лучше альтернатива"
        }

        return scores.tolist(), debug