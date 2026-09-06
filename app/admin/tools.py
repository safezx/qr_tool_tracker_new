"""CRUD инструментов."""

from sqlalchemy.exc import IntegrityError

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..models import Tool
from ..utils.audit import log_action
from . import admin_bp
from .forms import DEFAULT_TOOL_CATEGORIES, ToolForm


@admin_bp.route("/tools")
def tools_list():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()

    query = Tool.query
    if search:
        query = query.filter(Tool.name.ilike(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    if status == "available":
        query = query.filter_by(is_available=True)
    elif status == "taken":
        query = query.filter_by(is_available=False)

    tools = query.order_by(Tool.id.desc()).all()
    all_categories = sorted({t.category for t in Tool.query.all() if t.category})

    stats = {
        "total": Tool.query.count(),
        "available": Tool.query.filter_by(is_available=True).count(),
        "taken": Tool.query.filter_by(is_available=False).count(),
    }

    return render_template(
        "admin/tools_list.html",
        tools=tools,
        categories=all_categories,
        stats=stats,
        search=search,
        category=category,
        status=status,
    )


@admin_bp.route("/tools/add", methods=["GET", "POST"])
def add_tool():
    form = ToolForm()

    if form.validate_on_submit():
        tool = Tool()
        _apply_tool_form(tool, form)

        db.session.add(tool)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Инструмент с таким серийным номером уже существует.", "error")
            return render_template(
                "admin/tool_form.html", form=form, tool=None, categories=DEFAULT_TOOL_CATEGORIES
            )

        log_action("admin", current_user.full_name, "create", "tool", tool.id, tool.name)
        flash(f'Инструмент «{tool.name}» добавлен. QR-код: {tool.qr_code}.', "success")
        return redirect(url_for("admin.tools_list"))

    return render_template(
        "admin/tool_form.html", form=form, tool=None, categories=DEFAULT_TOOL_CATEGORIES
    )


@admin_bp.route("/tools/<int:tool_id>/edit", methods=["GET", "POST"])
def edit_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    form = ToolForm(obj=tool)

    if form.validate_on_submit():
        _apply_tool_form(tool, form)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Инструмент с таким серийным номером уже существует.", "error")
            return render_template(
                "admin/tool_form.html", form=form, tool=tool, categories=DEFAULT_TOOL_CATEGORIES
            )

        log_action("admin", current_user.full_name, "update", "tool", tool.id, tool.name)
        flash(f'Инструмент «{tool.name}» обновлён.', "success")
        return redirect(url_for("admin.tools_list"))

    return render_template(
        "admin/tool_form.html", form=form, tool=tool, categories=DEFAULT_TOOL_CATEGORIES
    )


@admin_bp.route("/tools/<int:tool_id>/delete", methods=["POST"])
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)

    if not tool.is_available:
        flash(f'Нельзя удалить «{tool.name}» — сейчас выдан.', "error")
        return redirect(url_for("admin.tools_list"))

    name = tool.name
    db.session.delete(tool)
    db.session.commit()
    log_action("admin", current_user.full_name, "delete", "tool", tool_id, name)
    flash(f'Инструмент «{name}» удалён.', "success")
    return redirect(url_for("admin.tools_list"))


def _apply_tool_form(tool, form):
    """Переносим данные из формы в объект Tool — явно, поле за полем,
    чтобы не полагаться на "магический" populate_obj()."""
    tool.name = form.name.data.strip()
    tool.category = (form.category.data or "").strip() or None
    tool.description = (form.description.data or "").strip() or None
    tool.location = (form.location.data or "").strip() or None
    tool.storage_place = (form.storage_place.data or "").strip() or None
    tool.serial_number = (form.serial_number.data or "").strip() or None
    tool.model = (form.model.data or "").strip() or None
    tool.manufacturer = (form.manufacturer.data or "").strip() or None
    tool.price = form.price.data
    tool.purchase_date = form.purchase_date.data
    tool.warranty_until = form.warranty_until.data
