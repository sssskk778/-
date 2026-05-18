from flask import jsonify


class AppError(ValueError):
    """Базовый класс для бизнес-ошибок приложения."""
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """Объект не найден."""
    status_code = 404

    def __init__(self, what: str = 'Объект'):
        super().__init__(f'{what} не найден')


class ValidationError(AppError):
    """Ошибка валидации бизнес-данных."""
    status_code = 422


class ConflictError(AppError):
    """Конфликт данных (дубликат и т.п.)."""
    status_code = 409


class CalculationError(AppError):
    """Ошибка при выполнении расчёта."""
    status_code = 400


def register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'ok': False, 'error': 'Не найдено'}), 404

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'ok': False, 'error': 'Нет доступа'}), 403

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'ok': False, 'error': 'Метод не разрешён'}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'ok': False, 'error': 'Внутренняя ошибка сервера'}), 500