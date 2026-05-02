# tests/test_api.py
"""
Тестирование API-эндпоинтов.
Проверяется доступность страниц и корректность HTTP-статусов.
"""

def test_login_page(client):
    """
    - Тестируется Get запрос по адресу: [/login]
    - Проверяется код ответа
    - Код результата должен быть [200]
    """
    # Arrange
    # Act
    response = client.get('/login')
    # Assert
    assert response.status_code == 200


def test_login_post_wrong_password(client):
    """
    - Тестируется Post запрос по адресу: [/login] с неверным паролем
    - Проверяется код ответа
    - Код результата должен быть [401]
    """
    # Arrange
    # Act
    response = client.post('/login', data={'username': 'admin', 'password': 'wrong'})
    # Assert
    assert response.status_code == 401


def test_login_post_empty_fields(client):
    """
    - Тестируется Post запрос по адресу: [/login] с пустыми полями
    - Проверяется код ответа
    - Код результата должен быть [401]
    """
    # Arrange
    # Act
    response = client.post('/login', data={'username': '', 'password': ''})
    # Assert
    assert response.status_code == 401


def test_login_post_success(client):
    """
    - Тестируется Post запрос по адресу: [/login] с корректными данными
    - Проверяется редирект на главную страницу
    - Код результата должен быть [302], редирект на [/]
    """
    # Arrange
    # Act
    response = client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Assert
    assert response.status_code == 302
    assert response.headers['Location'] == '/'


def test_register_page(client):
    """
    - Тестируется Get запрос по адресу: [/register]
    - Проверяется код ответа
    - Код результата должен быть [200]
    """
    # Arrange
    # Act
    response = client.get('/register')
    # Assert
    assert response.status_code == 200


def test_register_post_empty_fields(client):
    """
    - Тестируется Post запрос по адресу: [/register] с пустыми полями
    - Проверяется код ответа
    - Код результата должен быть [400]
    """
    # Arrange
    # Act
    response = client.post('/register', data={'username': '', 'full_name': '', 'password': ''})
    # Assert
    assert response.status_code == 400


def test_register_post_short_password(client):
    """
    - Тестируется Post запрос по адресу: [/register] с коротким паролем
    - Проверяется код ответа
    - Код результата должен быть [400]
    """
    # Arrange
    # Act
    response = client.post('/register', data={'username': 'test', 'full_name': 'Test', 'password': '123'})
    # Assert
    assert response.status_code == 400


def test_register_post_success(client):
    import random
    uid = random.randint(10000, 99999)
    response = client.post('/register', data={
        'username': f'newuser{uid}',
        'full_name': 'New User',
        'password': '123456'
    })
    assert response.status_code == 302
    assert response.headers['Location'] == '/'

def test_criteria_api_authorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/criteria] с авторизацией
    - Проверяется код ответа и содержимое
    - Код результата должен быть [200], ответ содержит JSON с критериями
    """
    # Arrange
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Act
    response = client.get('/api/criteria')
    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 10
    assert data[0]['code'] == 'on_time_rate'


def test_carriers_api_authorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/carriers] с авторизацией
    - Проверяется код ответа
    - Код результата должен быть [200]
    """
    # Arrange
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Act
    response = client.get('/api/carriers')
    # Assert
    assert response.status_code == 200


def test_datasets_api_authorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/datasets] с авторизацией
    - Проверяется код ответа
    - Код результата должен быть [200]
    """
    # Arrange
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Act
    response = client.get('/api/datasets')
    # Assert
    assert response.status_code == 200


def test_scenarios_api_authorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/scenarios] с авторизацией
    - Проверяется код ответа
    - Код результата должен быть [200]
    """
    # Arrange
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Act
    response = client.get('/api/scenarios')
    # Assert
    assert response.status_code == 200


def test_auth_me_authorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/auth/me] с авторизацией
    - Проверяется код ответа и данные пользователя
    - Код результата должен быть [200], username = 'admin'
    """
    # Arrange
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Act
    response = client.get('/api/auth/me')
    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'admin'
    assert data['role'] == 'admin'


def test_auth_me_unauthorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/auth/me] без авторизации
    - Проверяется редирект на страницу входа
    - Код результата должен быть [302]
    """
    # Arrange
    # Act
    response = client.get('/api/auth/me')
    # Assert
    assert response.status_code == 302


def test_criteria_api_unauthorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/criteria] без авторизации
    - Проверяется редирект
    - Код результата должен быть [302]
    """
    # Arrange
    # Act
    response = client.get('/api/criteria')
    # Assert
    assert response.status_code == 302


def test_carriers_api_unauthorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/carriers] без авторизации
    - Проверяется редирект
    - Код результата должен быть [302]
    """
    # Arrange
    # Act
    response = client.get('/api/carriers')
    # Assert
    assert response.status_code == 302


def test_datasets_api_unauthorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/datasets] без авторизации
    - Проверяется редирект
    - Код результата должен быть [302]
    """
    # Arrange
    # Act
    response = client.get('/api/datasets')
    # Assert
    assert response.status_code == 302


def test_scenarios_api_unauthorized(client):
    """
    - Тестируется Get запрос по адресу: [/api/scenarios] без авторизации
    - Проверяется редирект
    - Код результата должен быть [302]
    """
    # Arrange
    # Act
    response = client.get('/api/scenarios')
    # Assert
    assert response.status_code == 302


def test_logout(client):
    """
    - Тестируется Get запрос по адресу: [/logout]
    - Проверяется редирект на страницу входа
    - Код результата должен быть [302]
    """
    # Arrange
    # Act
    response = client.get('/logout')
    # Assert
    assert response.status_code == 302