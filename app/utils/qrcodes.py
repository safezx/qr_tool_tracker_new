"""
Генерация QR-кодов для инструментов.

QR-код кодирует не сам идентификатор, а полную ссылку на карточку
инструмента (SITE_URL + /tool/<код>) — так отсканировавший телефон сразу
открывает нужную страницу, без дополнительного приложения.
"""

import io

import qrcode


def build_tool_url(site_url, qr_code):
    return f"{site_url.rstrip('/')}/tool/{qr_code}"


def generate_qr_png(data, box_size=8, border=2):
    """Возвращает PNG-картинку QR-кода как байты."""
    img = qrcode.make(data, box_size=box_size, border=border)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
