"""
Фабрика приложения Flask.

create_app() собирает приложение из частей: конфигурация, расширения
(база данных, логин, CSRF), блюпринты (auth / employee / admin) и
обработчики ошибок. Такой подход (application factory) — стандартная
практика Flask, которая упрощает тестирование и повторный запуск.
"""

from pathlib import Path

from flask import Flask, render_template

from config import Config

from .extensions import csrf, db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_helpers(app)
    _register_cli(app)

    return app


def _init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Пожалуйста, войдите, чтобы продолжить."
    login_manager.login_message_category = "warning"

    from .models import Admin, Employee

    @login_manager.user_loader
    def load_user(prefixed_id):
        # Admin и Employee — разные таблицы, но оба логинятся через
        # Flask-Login. Чтобы не перепутать "admin:3" и "employee:3",
        # get_id() каждой модели возвращает id с префиксом роли (см.
        # app/models.py), а здесь префикс разбирается обратно.
        role, _, raw_id = prefixed_id.partition(":")
        if role == "admin":
            return db.session.get(Admin, int(raw_id))
        if role == "employee":
            return db.session.get(Employee, int(raw_id))
        return None


def _register_blueprints(app):
    from .admin import admin_bp
    from .auth import auth_bp
    from .employee import employee_bp
    from .employee_auth import employee_auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500


def _register_template_helpers(app):
    from .utils.time import format_moscow, moscow_now

    @app.context_processor
    def inject_helpers():
        return dict(moscow_now=moscow_now, format_moscow=format_moscow)


def _register_cli(app):
    from .cli import register_cli_commands

    register_cli_commands(app)
