"""
Аудит-лог: кто, когда и что сделал в системе.

log_action() — единственная точка записи в журнал. Вызывается уже ПОСЛЕ
того, как основное действие сохранено в базу, и сама сразу коммитит запись —
вызывающему коду не нужно помнить о состоянии сессии.
"""

from ..extensions import db
from ..models import AuditLog

ACTOR_ADMIN = "admin"
ACTOR_EMPLOYEE = "employee"
ACTOR_SYSTEM = "system"


def log_action(actor_type, actor_name, action, entity_type, entity_id=None, details=None):
    entry = AuditLog(
        actor_type=actor_type,
        actor_name=actor_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()
