"""
Локальный запуск для разработки: python run.py

Использует встроенный сервер Flask (с автоперезагрузкой при изменении
кода). Для более надёжного запуска (и в будущем — на сервере) используйте
wsgi.py + waitress, см. README.md.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
