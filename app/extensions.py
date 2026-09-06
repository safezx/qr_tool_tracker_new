"""
Экземпляры расширений Flask.

Вынесены в отдельный файл (а не создаются прямо в __init__.py), чтобы их
можно было импортировать из любого модуля (models.py, routes и т.д.) без
циклических импортов — привычный паттерн для Flask-приложений с фабрикой.
"""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
