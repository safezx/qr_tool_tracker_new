"""
Конфигурация приложения.

Все параметры, которые могут отличаться между окружениями (разработка,
локальный запуск, будущий сервер), берутся из переменных окружения (.env).
Так секреты не попадают в код и не требуют правки файлов при переносе
проекта на другой компьютер/сервер.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта — папка, где лежит этот файл.
BASE_DIR = Path(__file__).resolve().parent

# Подхватываем .env, если он есть (локальная разработка).
load_dotenv(BASE_DIR / ".env")


def _env_int(name, default):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return int(value)


class Config:
    # Секретный ключ нужен для сессий (в т.ч. логина администратора) и CSRF-защиты форм.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")

    # По умолчанию — SQLite-файл в instance/. Можно переопределить через .env,
    # например при переходе на сервер с более мощной СУБД.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + str((BASE_DIR / "instance" / "tool_tracker.db")),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Публичный адрес сайта — используется при формировании ссылок в QR-кодах.
    SITE_URL = os.environ.get("SITE_URL", "http://localhost:5001")

    # Сроки возврата инструмента, которые сотрудник может выбрать при выдаче.
    DEFAULT_RETURN_DAYS = _env_int("DEFAULT_RETURN_DAYS", 7)
    MAX_RETURN_DAYS = _env_int("MAX_RETURN_DAYS", 30)

    WTF_CSRF_ENABLED = True

    # Сотрудник входит на своём телефоне редко — сессия держится подолгу
    # (через "remember me" cookie Flask-Login). У администратора сессия
    # обычная: она задаётся только для входа сотрудников (см. login_user
    # с remember=True в app/employee_auth/routes.py).
    EMPLOYEE_REMEMBER_DAYS = _env_int("EMPLOYEE_REMEMBER_DAYS", 90)
    REMEMBER_COOKIE_DURATION = timedelta(days=EMPLOYEE_REMEMBER_DAYS)
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True

    # Cookie с флагом Secure браузер отправляет только по HTTPS. Локально
    # (http://localhost) это включать нельзя — cookie перестанут работать.
    # Как только проект окажется на сервере с HTTPS (см. README про Caddy),
    # поставьте FORCE_HTTPS_COOKIES=true в .env.
    FORCE_HTTPS_COOKIES = os.environ.get("FORCE_HTTPS_COOKIES", "false").lower() == "true"
    SESSION_COOKIE_SECURE = FORCE_HTTPS_COOKIES
    REMEMBER_COOKIE_SECURE = FORCE_HTTPS_COOKIES


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
