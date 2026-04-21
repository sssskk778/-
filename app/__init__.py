from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # ← ДОБАВИТЬ

_db = SQLAlchemy()
db = _db
migrate = Migrate()  # ← ДОБАВИТЬ

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object('config.Config')
    _db.init_app(app)
    migrate.init_app(app, _db)  # ← ДОБАВИТЬ

    from app.routes.auth import auth_bp
    from app.routes.web import web_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    from app.auth import current_user
    @app.context_processor
    def inject_user():
        return {'current_user': current_user()}

    return app