from flask import jsonify

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