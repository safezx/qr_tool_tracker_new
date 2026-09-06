from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import Admin
from ..utils.audit import log_action
from ..utils.time import moscow_now
from . import auth_bp
from .forms import LoginForm


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.is_active and admin.check_password(form.password.data):
            login_user(admin)
            admin.last_login_at = moscow_now()
            from ..extensions import db

            db.session.commit()
            log_action("admin", admin.full_name, "login", "admin", admin.id)

            next_url = request.args.get("next")
            return redirect(next_url or url_for("admin.dashboard"))

        flash("Неверный логин или пароль.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    log_action("admin", current_user.full_name, "logout", "admin", current_user.id)
    logout_user()
    flash("Вы вышли из системы.", "success")
    return redirect(url_for("auth.login"))
