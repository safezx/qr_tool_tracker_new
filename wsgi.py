"""
Точка входа для "боевого" запуска (без режима отладки Flask).

Запуск через waitress (чистый Python WSGI-сервер, без танцев вокруг
gunicorn/Windows):

    python wsgi.py

или явно:

    waitress-serve --host=0.0.0.0 --port=5001 wsgi:app
"""

import os

from waitress import serve

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5001))
    print(f"Сервер запущен: http://{host}:{port}")
    serve(app, host=host, port=port)
