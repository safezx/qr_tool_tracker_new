"""
Модели данных.

- Admin        — администратор (именной аккаунт, вход по логину/паролю).
- Employee     — сотрудник (тоже вход по логину/паролю — табельный номер
                 используется как логин, пароль выдаёт администратор).
- Tool         — инструмент.
- ToolRequest  — заявка на выдачу инструмента (взятие/возврат).
- AuditLog     — журнал действий (кто/когда/что).

Заявка называется ToolRequest, а не Request — специально, чтобы не путать
с объектом запроса Flask (flask.request), как это было в старой версии.

И Admin, и Employee умеют логиниться через Flask-Login, поэтому у обоих
есть свой password_hash и свой get_id(). Чтобы Flask-Login не перепутал
администратора с сотрудником с тем же числовым id, get_id() возвращает
идентификатор с префиксом ("admin:3" / "employee:3"), а в user_loader
(app/__init__.py) префикс разбирается обратно. Атрибут role — простой
Python-признак (не колонка в БД), по нему шаблоны и before_request-проверки
понимают, кто именно сейчас вошёл.
"""

import secrets

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .utils.time import moscow_now


def generate_qr_code():
    """Короткий, непредсказуемый идентификатор инструмента для QR-кода."""
    return secrets.token_hex(4).upper()  # например, "A3F9C21B"


class Admin(UserMixin, db.Model):
    """Администратор системы. У каждого — свой логин, для аудит-лога."""

    __tablename__ = "admins"

    role = "admin"  # не колонка — просто признак роли для Flask-Login/шаблонов

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=moscow_now, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin:{self.id}"

    def __repr__(self):
        return f"<Admin {self.username}>"


class Employee(UserMixin, db.Model):
    """Сотрудник, который берёт и возвращает инструменты. Логин — табельный
    номер, пароль выдаёт администратор (см. app/admin/employees.py)."""

    __tablename__ = "employees"

    role = "employee"  # не колонка — просто признак роли для Flask-Login/шаблонов

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    employee_number = db.Column(db.String(20), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=moscow_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=moscow_now, onupdate=moscow_now, nullable=False)

    # Пароль выдаётся администратором (см. generate_temp_password), поэтому
    # nullable=True — у ещё не настроенного сотрудника пароля может не быть.
    password_hash = db.Column(db.String(255), nullable=True)
    # Каждый пароль, который задаёт администратор, — временный: сотрудник
    # обязан сменить его при первом входе (app/employee_auth).
    must_change_password = db.Column(db.Boolean, default=True, nullable=False)

    requests = db.relationship(
        "ToolRequest", backref="employee", lazy=True, cascade="all, delete-orphan"
    )

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"employee:{self.id}"

    def __repr__(self):
        return f"<Employee {self.full_name()}>"


class Tool(db.Model):
    """Инструмент, который можно взять и вернуть."""

    __tablename__ = "tools"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)

    qr_code = db.Column(db.String(20), unique=True, nullable=False, default=generate_qr_code)

    location = db.Column(db.String(100), nullable=True)
    storage_place = db.Column(db.String(100), nullable=True)

    is_available = db.Column(db.Boolean, default=True, nullable=False)

    serial_number = db.Column(db.String(50), unique=True, nullable=True)
    model = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    price = db.Column(db.Float, nullable=True)
    warranty_until = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=moscow_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=moscow_now, onupdate=moscow_now, nullable=False)

    requests = db.relationship(
        "ToolRequest", backref="tool", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def active_request(self):
        for r in self.requests:
            if r.status == ToolRequest.STATUS_APPROVED:
                return r
        return None

    def __repr__(self):
        return f"<Tool {self.name} ({self.qr_code})>"


class ToolRequest(db.Model):
    """Заявка на выдачу инструмента. Создаётся сразу в статусе 'выдан'."""

    __tablename__ = "tool_requests"

    STATUS_APPROVED = "approved"
    STATUS_RETURNED = "returned"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey("tools.id"), nullable=False)

    request_time = db.Column(db.DateTime, default=moscow_now, nullable=False)
    expected_return_date = db.Column(db.Date, nullable=False)
    actual_return_time = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(20), default=STATUS_APPROVED, nullable=False)

    purpose = db.Column(db.Text, nullable=True)
    condition_before = db.Column(db.Text, nullable=True)
    condition_after = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)

    def mark_returned(self, condition_after=None, notes=None):
        self.status = self.STATUS_RETURNED
        self.actual_return_time = moscow_now()
        if self.tool:
            self.tool.is_available = True
        if condition_after:
            self.condition_after = condition_after
        if notes:
            self.admin_notes = notes

    @property
    def usage_days(self):
        if not self.request_time:
            return None
        end = self.actual_return_time or moscow_now()
        return max((end - self.request_time).days, 0)

    @property
    def is_overdue(self):
        if self.status != self.STATUS_APPROVED or not self.expected_return_date:
            return False
        return moscow_now().date() > self.expected_return_date

    def __repr__(self):
        return f"<ToolRequest {self.id}: {self.status}>"


class AuditLog(db.Model):
    """Журнал действий: кто, когда и что сделал."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=moscow_now, nullable=False)
    actor_type = db.Column(db.String(20), nullable=False)  # admin / employee / system
    actor_name = db.Column(db.String(150), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # create / update / delete / take / return / login ...
    entity_type = db.Column(db.String(50), nullable=False)  # tool / employee / admin
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.timestamp} {self.actor_type}:{self.action} {self.entity_type}#{self.entity_id}>"
