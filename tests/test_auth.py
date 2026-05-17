"""
Сценарий 1: Авторизация и управление сессией.
Файл: tests/test_auth.py
"""
import json


class TestAuthentication:

    def test_case1_login_success(self, client):
        """
        TestCase1. POST /api/auth/login с корректными данными администратора.
        Ожидание: статус 200, сессия установлена, возвращены данные пользователя.
        """
        response = client.post('/api/auth/login',
                                data=json.dumps({'username': 'admin', 'password': 'admin123'}),
                                content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['data']['username'] == 'admin'
        assert data['data']['role'] == 'admin'

    def test_case2_login_wrong_password(self, client):
        """
        TestCase2. POST /api/auth/login с некорректным паролем.
        Ожидание: статус 401, сообщение об ошибке.
        """
        response = client.post('/api/auth/login',
                                data=json.dumps({'username': 'admin', 'password': 'wrongpass'}),
                                content_type='application/json')
        assert response.status_code == 401
        data = response.get_json()
        assert data['ok'] is False
        assert 'error' in data

    def test_case3_protected_endpoint_without_auth(self, client):
        """
        TestCase3. GET на защищённый эндпоинт без авторизации.
        Ожидание: статус 401, доступ запрещён.
        """
        response = client.get('/api/datasets')
        assert response.status_code == 401