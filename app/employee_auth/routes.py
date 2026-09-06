from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from ..extensions import db
from ..models import Employee
from ..utils.audit import log_action
from . import employee_auth_bp
from .forms import ChangePasswordForm, EmployeeLoginForm


@employee_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and getattr(current_user, "role", None) == "employee":
        return redirect(url_for("employee.home"))

    form = EmployeeLoginForm()
    if form.validate_on_submit():
        number = form.employee_number.data.strip()
        employee = Employee.query.filter_by(employee_number=number).first()

        if employee and employee.is_active and employee.check_password(form.password.data):
            login_user(employee, remember=True)
            log_action("employee", employee.full_name(), "login", "employee", employee.id)

            if employee.must_change_password:
                flash("Это временный пароль. Задайте новый, чтобы продолжить.", "warning")
                return redirect(url_for("employee_auth.change_password"))

            next_url = request.args.get("next")
            return redirect(next_url or url_for("employee.home"))

        flash("Неверный табельный номер или пароль.", "error")

    return render_template("employee_auth/login.html", form=form)


@employee_auth_bp.route("/logout", methods=["POST"])
def logout():
    log_action("employee", current_user.full_name(), "logout", "employee", current_user.id)
    logout_user()
    flash("Вы вышли из системы.", "success")
    return redirect(url_for("employee.home"))


@employee_auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Текущий пароль указан неверно.", "error")
        else:
            current_user.set_password(form.new_password.data)
            current_user.must_change_password = False
            db.session.commit()
            log_action(
                "employee", current_user.full_name(), "change_password", "employee", current_user.id
            )
            flash("Пароль обновлён.", "success")
            return redirect(url_for("employee.home"))

    return render_template("employee_auth/change_password.html", form=form)
