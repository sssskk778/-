"""
Модуль декораторов валидации запросов.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError


def validate_body(schema_cls):
    """Декоратор: валидирует JSON-тело запроса через Marshmallow-схему."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = schema_cls().load(request.get_json(silent=True) or {})
            except ValidationError as e:
                return jsonify({'ok': False, 'error': 'Ошибка валидации', 'details': e.messages}), 422
            return f(*args, data=data, **kwargs)
        return wrapper
    return decorator


def validate_query(schema_cls):
    """Декоратор: валидирует query-параметры через Marshmallow-схему."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                filters = schema_cls().load(request.args.to_dict())
            except ValidationError as e:
                return jsonify({'ok': False, 'error': 'Ошибка параметров запроса', 'details': e.messages}), 422
            return f(*args, filters=filters, **kwargs)
        return wrapper
    return decorator