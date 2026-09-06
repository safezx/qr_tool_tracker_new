"""Просмотр журнала действий (аудит-лог)."""

from flask import render_template, request

from ..models import AuditLog
from . import admin_bp


@admin_bp.route("/audit-log")
def audit_log():
    actor_type = request.args.get("actor_type", "")
    entity_type = request.args.get("entity_type", "")

    query = AuditLog.query
    if actor_type:
        query = query.filter_by(actor_type=actor_type)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)

    entries = query.order_by(AuditLog.timestamp.desc()).limit(300).all()

    return render_template(
        "admin/audit_log.html",
        entries=entries,
        actor_type=actor_type,
        entity_type=entity_type,
    )
