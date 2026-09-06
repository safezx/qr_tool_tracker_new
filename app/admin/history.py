"""Страница истории возвратов и простой статистики использования.

Фильтрация делается в Python, а не в SQL: записей — десятки/сотни, а не
миллионы, зато код проще читать и менять начинающему разработчику.
"""

from collections import Counter

from flask import render_template, request

from ..models import ToolRequest
from . import admin_bp


@admin_bp.route("/history")
def history():
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    search = request.args.get("search", "").strip()

    returned = (
        ToolRequest.query.filter_by(status=ToolRequest.STATUS_RETURNED)
        .order_by(ToolRequest.actual_return_time.desc())
        .all()
    )

    if date_from:
        returned = [
            r for r in returned
            if r.actual_return_time and r.actual_return_time.date().isoformat() >= date_from
        ]
    if date_to:
        returned = [
            r for r in returned
            if r.actual_return_time and r.actual_return_time.date().isoformat() <= date_to
        ]
    if search:
        s = search.lower()
        returned = [
            r for r in returned
            if (r.tool and s in r.tool.name.lower())
            or (r.employee and s in r.employee.full_name().lower())
        ]

    total_returned = len(returned)
    total_usage_days = sum(r.usage_days or 0 for r in returned)
    avg_usage_days = round(total_usage_days / total_returned, 1) if total_returned else 0

    top_tools = Counter(r.tool.name for r in returned if r.tool).most_common(5)
    top_employees = Counter(r.employee.full_name() for r in returned if r.employee).most_common(5)

    return render_template(
        "admin/history.html",
        requests=returned,
        total_returned=total_returned,
        total_usage_days=total_usage_days,
        avg_usage_days=avg_usage_days,
        top_tools=top_tools,
        top_employees=top_employees,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
