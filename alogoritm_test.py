"""
Верификация алгоритмов SWARA, TOPSIS, VIKOR.
Запуск из корня проекта: python verify_algorithms.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from app.services.algorithms.swara import SwaraService
from app.services.algorithms.topsis import TopsisService
from app.services.algorithms.vikor import VikorService

# =============================================================================
# ВХОДНЫЕ ДАННЫЕ (те же что в Excel)
# =============================================================================

matrix = np.array([
    [85.0, 4.2, 12.5],   # Перевозчик А
    [92.0, 3.8, 10.0],   # Перевозчик Б
    [78.0, 4.5, 14.0],   # Перевозчик В
])

carriers = ['Перевозчик А', 'Перевозчик Б', 'Перевозчик В']
criteria  = ['on_time_rate', 'feedback_score', 'rate_per_km']
kinds     = ['benefit', 'benefit', 'cost']
ranking   = ['on_time_rate', 'feedback_score', 'rate_per_km']
s_values  = [0.1, 0.2]

# Ожидаемые значения из Excel
EXPECTED_SWARA = {'on_time_rate': 0.3750, 'feedback_score': 0.3409, 'rate_per_km': 0.2841}
EXPECTED_TOPSIS_ORDER = ['Перевозчик Б', 'Перевозчик А', 'Перевозчик В']
EXPECTED_VIKOR_ORDER  = ['Перевозчик А', 'Перевозчик Б', 'Перевозчик В']

# =============================================================================
# SWARA
# =============================================================================

print('=' * 60)
print('  SWARA — расчёт весовых коэффициентов')
print('=' * 60)

weights_dict = SwaraService.compute(ranking, s_values)
weights = [weights_dict[c] for c in criteria]

print(f'{"Критерий":<25} {"Вес (код)":>12} {"Ожидание":>12} {"Совпадение":>12}')
print('-' * 63)
all_swara_ok = True
for c, w in zip(criteria, weights):
    exp = EXPECTED_SWARA[c]
    ok = abs(w - exp) < 0.001
    if not ok:
        all_swara_ok = False
    mark = '✓' if ok else '✗'
    print(f'{c:<25} {w:>12.4f} {exp:>12.4f} {mark:>12}')
print(f'{"Сумма весов:":<25} {sum(weights):>12.4f}')
print()

# =============================================================================
# TOPSIS
# =============================================================================

print('=' * 60)
print('  TOPSIS — ранжирование перевозчиков')
print('=' * 60)

scores_t, debug_t = TopsisService().compute(matrix, kinds, weights)

print(f'{"Перевозчик":<20} {"Cᵢ (код)":>10} {"S+":>10} {"S−":>10} {"Ранг":>6}')
print('-' * 58)

indexed_t = sorted(enumerate(carriers), key=lambda x: scores_t[x[0]], reverse=True)
topsis_order = []
for rank, (i, carrier) in enumerate(indexed_t, 1):
    topsis_order.append(carrier)
    dbg = debug_t[i]
    print(f'{carrier:<20} {scores_t[i]:>10.4f} '
          f'{dbg["distance_to_best"]:>10.4f} '
          f'{dbg["distance_to_worst"]:>10.4f} '
          f'{rank:>6}')

topsis_ok = topsis_order == EXPECTED_TOPSIS_ORDER
print(f'\nОжидаемый порядок: {" > ".join(EXPECTED_TOPSIS_ORDER)}')
print(f'Полученный порядок: {" > ".join(topsis_order)}')
print(f'Совпадение: {"✓ ВЕРНО" if topsis_ok else "✗ ОШИБКА"}')
print()

# =============================================================================
# VIKOR
# =============================================================================

print('=' * 60)
print('  VIKOR — ранжирование перевозчиков')
print('=' * 60)

scores_v, debug_v = VikorService().compute(matrix, kinds, weights)

s_vals = debug_v['S_values']
r_vals = debug_v['R_values']
q_vals = debug_v['Q_values']

print(f'{"Перевозчик":<20} {"Sᵢ":>8} {"Rᵢ":>8} {"Qᵢ":>8} {"Score":>10} {"Ранг":>6}')
print('-' * 65)

indexed_v = sorted(enumerate(carriers), key=lambda x: scores_v[x[0]], reverse=True)
vikor_order = []
for rank, (i, carrier) in enumerate(indexed_v, 1):
    vikor_order.append(carrier)
    print(f'{carrier:<20} {s_vals[i]:>8.4f} {r_vals[i]:>8.4f} '
          f'{q_vals[i]:>8.4f} {scores_v[i]:>10.4f} {rank:>6}')

vikor_ok = vikor_order == EXPECTED_VIKOR_ORDER
print(f'\nОжидаемый порядок: {" > ".join(EXPECTED_VIKOR_ORDER)}')
print(f'Полученный порядок: {" > ".join(vikor_order)}')
print(f'Совпадение: {"✓ ВЕРНО" if vikor_ok else "✗ ОШИБКА"}')
print()

# =============================================================================
# ИТОГ
# =============================================================================

print('=' * 60)
print('  Итог верификации')
print('=' * 60)
print(f'  SWARA  — сумма весов = 1:           {"✓ ВЕРНО" if abs(sum(weights)-1) < 1e-6 else "✗ ОШИБКА"}')
print(f'  SWARA  — веса совпадают с Excel:     {"✓ ВЕРНО" if all_swara_ok else "✗ ОШИБКА"}')
print(f'  TOPSIS — порядок совпадает с Excel:  {"✓ ВЕРНО" if topsis_ok else "✗ ОШИБКА"}')
print(f'  VIKOR  — порядок совпадает с Excel:  {"✓ ВЕРНО" if vikor_ok else "✗ ОШИБКА"}')