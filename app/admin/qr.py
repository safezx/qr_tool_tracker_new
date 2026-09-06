"""Просмотр, скачивание и печать QR-кодов инструментов."""

from flask import Response, current_app, render_template, request

from ..models import Tool
from ..utils.qrcodes import build_tool_url, generate_qr_png
from . import admin_bp


@admin_bp.route("/qr-codes")
def qr_list():
    tools = Tool.query.order_by(Tool.category, Tool.name).all()

    by_category = {}
    for tool in tools:
        by_category.setdefault(tool.category or "Без категории", []).append(tool)

    return render_template("admin/qr_codes.html", tools_by_category=by_category)


@admin_bp.route("/tools/<int:tool_id>/qr.png")
def qr_image(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    url = build_tool_url(current_app.config["SITE_URL"], tool.qr_code)
    png_bytes = generate_qr_png(url)

    response = Response(png_bytes, mimetype="image/png")
    if request.args.get("download"):
        response.headers["Content-Disposition"] = f"attachment; filename=qr_{tool.qr_code}.png"
    return response


@admin_bp.route("/qr-codes/print")
def qr_print():
    category = request.args.get("category", "").strip()

    query = Tool.query
    if category:
        query = query.filter_by(category=category)
    tools = query.order_by(Tool.category, Tool.name).all()

    return render_template("admin/qr_print.html", tools=tools, category=category)
