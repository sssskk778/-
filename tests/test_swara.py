# tests/test_swara.py
import pytest
from app.services.algorithms.swara import SwaraService

"""
Тестирование модуля расчета весов критериев методом SWARA.
Проверяется корректность вычислений и обработка исключений.
"""

def test_compute_simple():
    """
    - Тестируется метод compute с тремя критериями
    - Проверяется сумма весов и порядок важности
    - Сумма весов должна быть равна 1.0, веса должны убывать по порядку
    """
    # Arrange
    ranking = ['a', 'b', 'c']
    s_values = [0.2, 0.3]
    # Act
    weights = SwaraService.compute(ranking, s_values)
    # Assert
    assert sum(weights.values()) == pytest.approx(1.0, 0.01)
    assert weights['a'] > weights['b'] > weights['c']


def test_compute_two_criteria():
    """
    - Тестируется метод compute с двумя критериями
    - Проверяется количество весов и порядок
    - Должно быть 2 веса, первый больше второго
    """
    # Arrange
    ranking = ['x', 'y']
    s_values = [0.5]
    # Act
    weights = SwaraService.compute(ranking, s_values)
    # Assert
    assert len(weights) == 2
    assert weights['x'] > weights['y']


def test_compute_empty_ranking():
    """
    - Тестируется метод compute с пустым списком критериев
    - Проверяется выброс исключения ValueError
    """
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        SwaraService.compute([], [])


def test_compute_duplicates():
    """
    - Тестируется метод compute с дубликатами в ранжировании
    - Проверяется выброс исключения ValueError
    """
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        SwaraService.compute(['a', 'a'], [0.2])


def test_compute_wrong_s_values_count():
    """
    - Тестируется метод compute с неверным количеством s_values
    - Проверяется выброс исключения ValueError
    """
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        SwaraService.compute(['a', 'b', 'c'], [0.1])


def test_compute_negative_s_value():
    """
    - Тестируется метод compute с отрицательным значением s_values
    - Проверяется выброс исключения ValueError
    """
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        SwaraService.compute(['a', 'b'], [-0.1])


def test_compute_all_equal():
    """
    - Тестируется метод compute с нулевой сравнительной важностью
    - Проверяется равенство весов
    - Оба веса должны быть равны 0.5
    """
    # Arrange
    ranking = ['a', 'b']
    s_values = [0.0]
    # Act
    weights = SwaraService.compute(ranking, s_values)
    # Assert
    assert weights['a'] == weights['b'] == 0.5


def test_compute_big_s_value():
    """
    - Тестируется метод compute с большим значением s_values
    - Проверяется что первый вес больше второго
    """
    # Arrange
    ranking = ['a', 'b']
    s_values = [10.0]
    # Act
    weights = SwaraService.compute(ranking, s_values)
    # Assert
    assert weights['a'] > weights['b']


def test_validate_s_values():
    """
    - Тестируется метод validate_s_values
    - Проверяется валидация корректных и некорректных значений
    """
    # Arrange & Act & Assert
    assert SwaraService.validate_s_values([0.1, 0.5]) == True
    assert SwaraService.validate_s_values([-0.1]) == False
    assert SwaraService.validate_s_values('not_list') == False


def test_preview_weights():
    """
    - Тестируется метод preview_weights
    - Проверяется сумма весов
    - Сумма должна быть равна 1.0
    """
    # Arrange
    ranking = ['a', 'b']
    s_values = [0.5]
    # Act
    weights = SwaraService.preview_weights(ranking, s_values)
    # Assert
    assert sum(weights.values()) == pytest.approx(1.0, 0.01)