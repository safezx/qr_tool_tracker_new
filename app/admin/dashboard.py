"""Дашборд администратора: статистика + последние заявки + возврат."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..models import Employee, Tool, ToolRequest
from ..utils.audit import log_action
from . import admin_bp
from .forms import ReturnRequestForm


@admin_bp.route("/")
def dashboard():
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "").strip()

    query = ToolRequest.query
    if status_filter in (ToolRequest.STATUS_APPROVED, ToolRequest.STATUS_RETURNED):
        query = query.filter_by(status=status_filter)
    if search:
        query = query.join(Employee).filter(
            db.or_(
                Employee.first_name.ilike(f"%{search}%"),
                Employee.last_name.ilike(f"%{search}%"),
            )
        )

    requests_list = query.order_by(ToolRequest.request_time.desc()).limit(100).all()

    active_requests = ToolRequest.query.filter_by(status=ToolRequest.STATUS_APPROVED).all()

    stats = {
        "total_tools": Tool.query.count(),
        "available_tools": Tool.query.filter_by(is_available=True).count(),
        "active_requests": len(active_requests),
        "total_employees": Employee.query.filter_by(is_active=True).count(),
        "overdue": sum(1 for r in active_requests if r.is_overdue),
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        requests=requests_list,
        status_filter=status_filter,
        search=search,
    )


@admin_bp.route("/requests/<int:request_id>/return", methods=["GET", "POST"])
def return_request(request_id):
    tool_request = ToolRequest.query.get_or_404(request_id)

    if tool_request.status != ToolRequest.STATUS_APPROVED:
        flash("Эта заявка уже закрыта.", "error")
        return redirect(url_for("admin.dashboard"))

    form = ReturnRequestForm()
    if form.validate_on_submit():
        tool_name = tool_request.tool.name if tool_request.tool else "инструмент"
        tool_request.mark_returned(
            condition_after=form.condition_after.data, notes=form.notes.data
        )
        db.session.commit()

        log_action(
            "admin",
            current_user.full_name,
            "return",
            "tool",
            tool_request.tool_id,
            f"Заявка #{tool_request.id} закрыта администратором",
        )
        flash(f'Инструмент «{tool_name}» отмечен как возвращённый.', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/return_request.html", form=form, tool_request=tool_request)
