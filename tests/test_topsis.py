# tests/test_topsis.py
import numpy as np
import pytest
from app.services.topsis import TopsisService

"""
Тестирование метода многокритериальной оценки TOPSIS.
Проверяется корректность расчета и ранжирования.
"""

def test_topsis_simple():
    """3 альтернативы, benefit+cost, третья лучше первой"""
    topsis = TopsisService()
    matrix = np.array([[4, 6], [3, 4], [5, 3]])
    kinds = ['benefit', 'cost']
    weights = [0.5, 0.5]
    scores, debug = topsis.compute(matrix, kinds, weights)
    assert len(scores) == 3
    assert all(0 <= s <= 1 for s in scores)
    assert scores[2] > scores[0]


def test_topsis_benefit_only():
    """2 benefit, большие значения лучше"""
    topsis = TopsisService()
    matrix = np.array([[1, 2], [3, 4]])
    kinds = ['benefit', 'benefit']
    weights = [0.5, 0.5]
    scores, _ = topsis.compute(matrix, kinds, weights)
    assert scores[1] > scores[0]


def test_topsis_cost_only():
    """Все критерии cost — меньшие значения лучше"""
    topsis = TopsisService()
    matrix = np.array([[1, 2], [3, 4]])
    kinds = ['cost', 'cost']
    weights = [0.5, 0.5]
    scores, _ = topsis.compute(matrix, kinds, weights)
    assert scores[0] > scores[1]


def test_topsis_single_alternative():
    """Одна альтернатива — один score"""
    topsis = TopsisService()
    matrix = np.array([[5, 3]])
    kinds = ['benefit', 'cost']
    weights = [0.6, 0.4]
    scores, _ = topsis.compute(matrix, kinds, weights)
    assert len(scores) == 1


def test_topsis_debug_info():
    """Наличие distance_to_best, distance_to_worst, norm_values"""
    topsis = TopsisService()
    matrix = np.array([[4, 6], [3, 4]])
    kinds = ['benefit', 'cost']
    weights = [0.5, 0.5]
    scores, debug = topsis.compute(matrix, kinds, weights)
    assert 'distance_to_best' in debug[0]
    assert 'distance_to_worst' in debug[0]
    assert 'norm_values' in debug[0]


def test_topsis_all_same_values():
    """Одинаковые значения — равные score"""
    topsis = TopsisService()
    matrix = np.array([[5, 5], [5, 5]])
    kinds = ['benefit', 'benefit']
    weights = [0.5, 0.5]
    scores, _ = topsis.compute(matrix, kinds, weights)
    assert scores[0] == pytest.approx(scores[1], 0.01)


def test_topsis_extreme_weights():
    """Один вес = 1, другой = 0"""
    topsis = TopsisService()
    matrix = np.array([[1, 10], [10, 1]])
    kinds = ['benefit', 'cost']
    weights = [1.0, 0.0]
    scores, _ = topsis.compute(matrix, kinds, weights)
    assert scores[1] > scores[0]


def test_topsis_three_criteria():
    """3 критерия, разные веса"""
    topsis = TopsisService()
    matrix = np.array([[3, 4, 5], [5, 3, 2], [4, 5, 3]])
    kinds = ['benefit', 'benefit', 'cost']
    weights = [0.4, 0.3, 0.3]
    scores, _ = topsis.compute(matrix, kinds, weights)
    assert len(scores) == 3
    assert all(0 <= s <= 1 for s in scores)