import numpy as np
from typing import List, Tuple, Dict, Any


class TopsisService:
    """TOPSIS (векторная нормализация, без нормализации весов)"""

    def compute(
        self,
        raw_matrix: np.ndarray,
        kinds: List[str],
        weights: List[float]
    ) -> Tuple[List[float], List[Dict[str, Any]]]:

        X = np.array(raw_matrix, dtype=float)
        m, n = X.shape

        if m == 0:
            raise ValueError("Empty matrix")

        weights = np.array(weights, dtype=float)

        # 1. vector normalization
        denom = np.sqrt((X ** 2).sum(axis=0))
        denom = np.where(denom == 0, 1, denom)
        X_norm = X / denom

        # 2. weighting (NO normalization of weights)
        V = X_norm * weights

        # 3. ideal points
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

        # 4. distances
        d_pos = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
        d_neg = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))

        # 5. score
        eps = 1e-12
        score = d_neg / (d_pos + d_neg + eps)

        debug = [
            {
                "distance_to_best": float(d_pos[i]),
                "distance_to_worst": float(d_neg[i]),
                "score": float(score[i]),
                "raw_values": X[i].tolist(),
                "norm_values": X_norm[i].tolist(),
                "weighted_values": V[i].tolist(),
            }
            for i in range(m)
        ]

        return score.tolist(), debug