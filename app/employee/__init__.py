from flask import Blueprint, redirect, request, url_for
from flask_login import current_user

employee_bp = Blueprint("employee", __name__)


@employee_bp.before_request
def require_employee_login():
    """Главная страница остаётся публичной, всё остальное (карточка
    инструмента, взятие, возврат) — только для вошедшего сотрудника."""
    if request.endpoint == "employee.home":
        return None
    if not (
        current_user.is_authenticated
        and getattr(current_user, "role", None) == "employee"
        and current_user.is_active
    ):
        return redirect(url_for("employee_auth.login", next=request.path))


from . import routes  # noqa: E402,F401
