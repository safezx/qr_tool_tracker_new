from flask import Blueprint, redirect, request, url_for
from flask_login import current_user

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def require_login():
    """Все маршруты админки закрыты логином — проверяем это в одном месте,
    вместо того чтобы вешать @login_required на каждый view-метод.

    Важно проверять именно role == 'admin', а не просто is_authenticated:
    сотрудники тоже теперь логинятся через Flask-Login, и без этой проверки
    вошедший сотрудник мог бы попасть в админку."""
    if not (
        current_user.is_authenticated
        and getattr(current_user, "role", None) == "admin"
        and current_user.is_active
    ):
        return redirect(url_for("auth.login", next=request.path))


# Модули ниже регистрируют свои маршруты на admin_bp при импорте.
from . import audit  # noqa: E402,F401
from . import dashboard  # noqa: E402,F401
from . import employees  # noqa: E402,F401
from . import history  # noqa: E402,F401
from . import qr  # noqa: E402,F401
from . import tools  # noqa: E402,F401
