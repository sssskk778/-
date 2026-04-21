# app/services/swara.py
"""
Метод SWARA (Step-wise Weight Assessment Ratio Analysis)
для расчёта весов критериев на основе экспертного ранжирования
и сравнительной важности.
"""

class SwaraService:
    """Расчёт весов методом SWARA"""

    @staticmethod
    def compute(ranking: list[str], s_values: list[float]) -> dict[str, float]:
        """
        Рассчитывает веса критериев методом SWARA.

        :param ranking: Список кодов критериев от ВАЖНОГО к НЕВАЖНОМУ
        :param s_values: Список сравнительной важности s_j для j = 2..n
                         (на сколько процентов критерий j-1 важнее критерия j)
        :return: Словарь {code: weight}, сумма весов = 1
        """
        n = len(ranking)

        if len(s_values) != n - 1:
            raise ValueError(f"Ожидается {n - 1} значений s_values, получено {len(s_values)}")

        # Шаг 1: Коэффициенты k_j
        k = [1.0]  # k_1 = 1
        for s in s_values:
            if s < 0:
                raise ValueError(f"Сравнительная важность не может быть отрицательной: {s}")
            k.append(s + 1.0)

        # Шаг 2: Пересчитанные веса q_j
        q = [1.0]  # q_1 = 1
        for j in range(1, n):
            q.append(q[j - 1] / k[j])

        # Шаг 3: Нормализация
        total_q = sum(q)
        weights = {ranking[j]: q[j] / total_q for j in range(n)}

        return weights

    @staticmethod
    def validate_s_values(s_values: list[float]) -> bool:
        """Проверяет, что все s_values >= 0."""
        return all(s >= 0 for s in s_values)

    @staticmethod
    def preview_weights(ranking: list[str], s_values: list[float]) -> dict[str, float]:
        """
        Предварительный расчёт весов (без сохранения).
        Используется для динамического обновления в интерфейсе.
        """
        return SwaraService.compute(ranking, s_values)