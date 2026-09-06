"""
Публичный сценарий сотрудника: сканирование QR -> взятие/возврат инструмента.

Личность подтверждается логином (см. app/employee_auth) — сотрудник входит
один раз на своём телефоне, дальше все действия выполняются от его имени
через current_user, без повторного ввода ФИО.
"""

from datetime import timedelta

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..models import Tool, ToolRequest
from ..utils.audit import log_action
from ..utils.time import moscow_now
from . import employee_bp
from .forms import ReturnToolForm, TakeToolForm


@employee_bp.route("/")
def home():
    return render_template("employee/home.html")


@employee_bp.route("/tools")
def tools_catalog():
    """Список всех инструментов: свободен / занят (до какой даты, без имени
    держателя — это чужое дело), плюс отдельно то, что сейчас на руках у
    самого сотрудника. Взять инструмент отсюда нельзя — это по-прежнему
    делается только сканированием QR-кода на самом инструменте."""
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = Tool.query
    if search:
        query = query.filter(Tool.name.ilike(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    tools = query.order_by(Tool.category, Tool.name).all()

    all_categories = sorted({t.category for t in Tool.query.all() if t.category})

    rows = []
    my_rows = []
    for tool in tools:
        active_request = tool.active_request
        is_mine = bool(active_request and active_request.employee_id == current_user.id)
        row = {
            "tool": tool,
            "expected_return_date": active_request.expected_return_date if active_request else None,
            "is_overdue": active_request.is_overdue if active_request else False,
            "is_mine": is_mine,
        }
        rows.append(row)
        if is_mine:
            my_rows.append(row)

    return render_template(
        "employee/catalog.html",
        rows=rows,
        my_rows=my_rows,
        categories=all_categories,
        search=search,
        category=category,
    )


@employee_bp.route("/tool/<code>")
def tool_view(code):
    tool = Tool.query.filter_by(qr_code=code).first_or_404()

    take_form = None
    return_form = None
    active_request = None
    today = moscow_now().date()
    max_date = today + timedelta(days=current_app.config["MAX_RETURN_DAYS"])

    if tool.is_available:
        take_form = TakeToolForm()
        if not take_form.return_date.data:
            default_days = current_app.config["DEFAULT_RETURN_DAYS"]
            take_form.return_date.data = (moscow_now() + timedelta(days=default_days)).date()
    else:
        active_request = tool.active_request
        # Форму возврата показываем, только если инструмент выдан именно
        # текущему сотруднику — вернуть чужой инструмент можно только через
        # администратора (см. app/admin/dashboard.py).
        if active_request and active_request.employee_id == current_user.id:
            return_form = ReturnToolForm()

    return render_template(
        "employee/tool.html",
        tool=tool,
        take_form=take_form,
        return_form=return_form,
        active_request=active_request,
        today_str=today.isoformat(),
        max_date_str=max_date.isoformat(),
    )


@employee_bp.route("/tool/<code>/take", methods=["POST"])
def take_tool(code):
    tool = Tool.query.filter_by(qr_code=code).first_or_404()

    if not tool.is_available:
        flash("Инструмент уже занят.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    form = TakeToolForm()
    if not form.validate_on_submit():
        flash("Проверьте правильность заполнения формы.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    today = moscow_now().date()
    max_days = current_app.config["MAX_RETURN_DAYS"]
    max_date = today + timedelta(days=max_days)

    if form.return_date.data < today:
        flash("Дата возврата не может быть в прошлом.", "error")
        return redirect(url_for("employee.tool_view", code=code))
    if form.return_date.data > max_date:
        flash(f"Максимальный срок выдачи — {max_days} дней.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    tool_request = ToolRequest(
        employee_id=current_user.id,
        tool_id=tool.id,
        purpose=form.purpose.data,
        expected_return_date=form.return_date.data,
        status=ToolRequest.STATUS_APPROVED,
    )
    tool.is_available = False
    db.session.add(tool_request)
    db.session.commit()

    log_action(
        "employee", current_user.full_name(), "take", "tool", tool.id, f"Заявка #{tool_request.id}"
    )
    flash(
        f'Инструмент «{tool.name}» выдан. Вернуть до {form.return_date.data.strftime("%d.%m.%Y")}.',
        "success",
    )
    return redirect(url_for("employee.tool_view", code=code))


@employee_bp.route("/tool/<code>/return", methods=["POST"])
def return_tool(code):
    tool = Tool.query.filter_by(qr_code=code).first_or_404()

    if tool.is_available:
        flash("Этот инструмент сейчас не выдан.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    active_request = tool.active_request
    if not active_request:
        flash("Активная заявка на этот инструмент не найдена.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    if active_request.employee_id != current_user.id:
        flash("Этот инструмент выдан другому сотруднику. Обратитесь к администратору.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    form = ReturnToolForm()
    if not form.validate_on_submit():
        flash("Проверьте правильность заполнения формы.", "error")
        return redirect(url_for("employee.tool_view", code=code))

    active_request.mark_returned(condition_after=form.condition_after.data, notes=form.notes.data)
    db.session.commit()

    log_action(
        "employee", current_user.full_name(), "return", "tool", tool.id, f"Заявка #{active_request.id}"
    )
    flash(f'Инструмент «{tool.name}» возвращён.', "success")
    return redirect(url_for("employee.tool_view", code=code))
