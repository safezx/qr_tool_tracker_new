"""CRUD сотрудников."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..models import Employee
from ..utils.audit import log_action
from ..utils.passwords import generate_temp_password
from ..utils.time import moscow_now
from . import admin_bp
from .forms import EmployeeForm


@admin_bp.route("/employees")
def employees_list():
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    status = request.args.get("status", "").strip()

    query = Employee.query
    if search:
        s = f"%{search}%"
        query = query.filter(
            db.or_(Employee.first_name.ilike(s), Employee.last_name.ilike(s))
        )
    if department:
        query = query.filter_by(department=department)
    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)

    employees = query.order_by(Employee.id.desc()).all()
    all_departments = sorted({e.department for e in Employee.query.all() if e.department})

    stats = {
        "total": Employee.query.count(),
        "active": Employee.query.filter_by(is_active=True).count(),
        "inactive": Employee.query.filter_by(is_active=False).count(),
    }

    return render_template(
        "admin/employees_list.html",
        employees=employees,
        departments=all_departments,
        stats=stats,
        search=search,
        department=department,
        status=status,
    )


@admin_bp.route("/employees/add", methods=["GET", "POST"])
def add_employee():
    form = EmployeeForm()

    if form.validate_on_submit():
        error = _check_uniqueness(form)
        if error:
            flash(error, "error")
            return render_template("admin/employee_form.html", form=form, employee=None)

        employee = Employee()
        _apply_employee_form(employee, form)
        employee.is_active = True  # новый сотрудник всегда активен

        temp_password = generate_temp_password()
        employee.set_password(temp_password)
        employee.must_change_password = True

        db.session.add(employee)
        db.session.commit()

        log_action(
            "admin", current_user.full_name, "create", "employee", employee.id, employee.full_name()
        )
        flash(
            f'Сотрудник «{employee.full_name()}» добавлен. '
            f'Временный пароль: {temp_password} — сообщите его сотруднику лично '
            f'(при первом входе система попросит его сменить).',
            "success",
        )
        return redirect(url_for("admin.employees_list"))

    return render_template("admin/employee_form.html", form=form, employee=None)


@admin_bp.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)

    if request.method == "GET":
        form.is_active.data = employee.is_active

    if form.validate_on_submit():
        error = _check_uniqueness(form, exclude_id=employee.id)
        if error:
            flash(error, "error")
            return render_template("admin/employee_form.html", form=form, employee=employee)

        _apply_employee_form(employee, form)
        employee.is_active = form.is_active.data
        employee.updated_at = moscow_now()
        db.session.commit()

        log_action(
            "admin", current_user.full_name, "update", "employee", employee.id, employee.full_name()
        )
        flash(f'Сотрудник «{employee.full_name()}» обновлён.', "success")
        return redirect(url_for("admin.employees_list"))

    return render_template("admin/employee_form.html", form=form, employee=employee)


@admin_bp.route("/employees/<int:employee_id>/toggle", methods=["POST"])
def toggle_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.is_active = not employee.is_active
    employee.updated_at = moscow_now()
    db.session.commit()

    status_text = "активирован" if employee.is_active else "деактивирован"
    log_action(
        "admin", current_user.full_name, "update", "employee", employee.id,
        f"{employee.full_name()} {status_text}",
    )
    flash(f'Сотрудник «{employee.full_name()}» {status_text}.', "success")
    return redirect(url_for("admin.employees_list"))


@admin_bp.route("/employees/<int:employee_id>/reset-password", methods=["POST"])
def reset_employee_password(employee_id):
    """Выдать сотруднику новый временный пароль (например, если забыл свой)."""
    employee = Employee.query.get_or_404(employee_id)

    temp_password = generate_temp_password()
    employee.set_password(temp_password)
    employee.must_change_password = True
    db.session.commit()

    log_action(
        "admin", current_user.full_name, "reset_password", "employee", employee.id, employee.full_name()
    )
    flash(
        f'Новый временный пароль для «{employee.full_name()}»: {temp_password} — сообщите лично.',
        "success",
    )
    return redirect(url_for("admin.employees_list"))


@admin_bp.route("/employees/<int:employee_id>/delete", methods=["POST"])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    name = employee.full_name()

    db.session.delete(employee)
    db.session.commit()

    log_action("admin", current_user.full_name, "delete", "employee", employee_id, name)
    flash(f'Сотрудник «{name}» и его заявки удалены.', "success")
    return redirect(url_for("admin.employees_list"))


def _apply_employee_form(employee, form):
    employee.first_name = form.first_name.data.strip()
    employee.last_name = form.last_name.data.strip()
    employee.email = (form.email.data or "").strip() or None
    employee.employee_number = (form.employee_number.data or "").strip() or None
    employee.department = (form.department.data or "").strip() or None
    employee.phone = (form.phone.data or "").strip() or None
    employee.position = (form.position.data or "").strip() or None


def _check_uniqueness(form, exclude_id=None):
    """Проверяем email и табельный номер на уникальность до сохранения —
    так пользователь сразу видит понятную причину ошибки."""
    email = (form.email.data or "").strip()
    employee_number = (form.employee_number.data or "").strip()

    if email:
        query = Employee.query.filter_by(email=email)
        if exclude_id:
            query = query.filter(Employee.id != exclude_id)
        if query.first():
            return "Сотрудник с таким email уже существует."

    if employee_number:
        query = Employee.query.filter_by(employee_number=employee_number)
        if exclude_id:
            query = query.filter(Employee.id != exclude_id)
        if query.first():
            return "Сотрудник с таким табельным номером уже существует."

    return None
