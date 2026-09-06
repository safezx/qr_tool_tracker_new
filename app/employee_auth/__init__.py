from flask import Blueprint, redirect, request, url_for
from flask_login import current_user

employee_auth_bp = Blueprint("employee_auth", __name__, url_prefix="/account")


@employee_auth_bp.before_request
def require_employee_for_protected_routes():
    """Логин остаётся открытым для всех, остальные маршруты этого блюпринта
    (логаут, смена пароля) — только для вошедшего сотрудника. Проверяем role,
    а не просто is_authenticated, — иначе вошедший администратор мог бы
    случайно попасть на страницу смены пароля сотрудника."""
    if request.endpoint == "employee_auth.login":
        return None
    if not (current_user.is_authenticated and getattr(current_user, "role", None) == "employee"):
        return redirect(url_for("employee_auth.login", next=request.path))


from . import routes  # noqa: E402,F401
