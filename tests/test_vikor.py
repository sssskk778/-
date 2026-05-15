# tests/test_vikor.py
import numpy as np
import pytest
from app.services.algorithms.vikor import VikorService

"""
Тестирование метода многокритериальной оценки VIKOR.
Проверяется корректность расчета и ранжирования.
"""

def test_vikor_simple():
    """3 альтернативы, benefit+cost, меньший score = лучше"""
    vikor = VikorService(v=0.5)
    matrix = np.array([[4, 6], [3, 4], [5, 3]])
    kinds = ['benefit', 'cost']
    weights = [0.5, 0.5]
    scores, debug = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 3
    assert all(0 <= s <= 1 for s in scores)
    best = scores.index(min(scores))
    assert best == 2


def test_vikor_two_alternatives():
    """2 альтернативы, 2 score"""
    vikor = VikorService()
    matrix = np.array([[1, 2], [3, 4]])
    kinds = ['benefit', 'benefit']
    weights = [0.5, 0.5]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 2


def test_vikor_cost_only():
    """Все критерии cost — меньшие значения лучше"""
    vikor = VikorService()
    matrix = np.array([[1, 2], [3, 4]])
    kinds = ['cost', 'cost']
    weights = [0.5, 0.5]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert scores[0] < scores[1]


def test_vikor_v_parameter():
    """v=0.0 — работает"""
    vikor = VikorService(v=0.0)
    matrix = np.array([[4, 6], [3, 4]])
    kinds = ['benefit', 'cost']
    weights = [0.5, 0.5]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 2


def test_vikor_v_one():
    """v=1.0 — работает"""
    vikor = VikorService(v=1.0)
    matrix = np.array([[4, 6], [3, 4]])
    kinds = ['benefit', 'cost']
    weights = [0.5, 0.5]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 2
    assert all(0 <= s <= 1 for s in scores)


def test_vikor_debug_info():
    """Наличие X_norm, S_values, R_values"""
    vikor = VikorService()
    matrix = np.array([[4, 6], [3, 4]])
    kinds = ['benefit', 'cost']
    weights = [0.5, 0.5]
    scores, debug = vikor.compute(matrix, kinds, weights)
    assert 'X_norm' in debug
    assert 'S_values' in debug
    assert 'R_values' in debug


def test_vikor_all_same():
    """Одинаковые значения — равные score"""
    vikor = VikorService()
    matrix = np.array([[5, 5], [5, 5]])
    kinds = ['benefit', 'benefit']
    weights = [0.5, 0.5]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert scores[0] == pytest.approx(scores[1], 0.01)


def test_vikor_single_alternative():
    """Одна альтернатива — один score"""
    vikor = VikorService()
    matrix = np.array([[5, 3]])
    kinds = ['benefit', 'cost']
    weights = [0.6, 0.4]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 1


def test_vikor_three_criteria():
    """3 критерия, разные веса"""
    vikor = VikorService(v=0.5)
    matrix = np.array([[3, 4, 5], [5, 3, 2], [4, 5, 3]])
    kinds = ['benefit', 'benefit', 'cost']
    weights = [0.4, 0.3, 0.3]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 3
    assert all(0 <= s <= 1 for s in scores)


def test_vikor_extreme_weights():
    """Один вес = 1, другие = 0"""
    vikor = VikorService()
    matrix = np.array([[1, 10], [10, 1]])
    kinds = ['benefit', 'cost']
    weights = [1.0, 0.0]
    scores, _ = vikor.compute(matrix, kinds, weights)
    assert len(scores) == 2