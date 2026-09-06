"""
Разовая генерация временных паролей для сотрудников, у которых их ещё нет
(актуально сразу после переноса из старой системы, где авторизации не было).

Запуск:
    python scripts/set_temp_passwords.py

Пароли не выводятся в консоль Windows (кириллица там может отображаться
некорректно) — вместо этого сохраняются в текстовый файл
instance/temp_passwords_<дата_время>.txt в кодировке UTF-8 (откройте его
в любом текстовом редакторе). Передайте пароли сотрудникам лично и удалите
файл после этого — держать пароли в текстовом файле дольше необходимого
не стоит.

Сотрудников без табельного номера скрипт пропускает и перечисляет отдельно:
табельный номер — это логин, без него задать пароль некому. Сначала
заполните табельный номер в админке (Сотрудники → Изменить), потом
запустите скрипт ещё раз — он не трогает уже настроенные пароли повторно.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Employee  # noqa: E402
from app.utils.passwords import generate_temp_password  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        without_password = Employee.query.filter(Employee.password_hash.is_(None)).all()

        skipped = [e for e in without_password if not e.employee_number]
        ready = [e for e in without_password if e.employee_number]

        if skipped:
            print("Пропущены (нет табельного номера — сначала заполните его в админке):")
            for e in skipped:
                print(f"  - {e.full_name()} (id={e.id})")

        if not ready:
            print("Нет сотрудников, которым нужно задать пароль.")
            return

        lines = ["Сотрудник;Табельный номер;Временный пароль"]
        for employee in ready:
            password = generate_temp_password()
            employee.set_password(password)
            employee.must_change_password = True
            lines.append(f"{employee.full_name()};{employee.employee_number};{password}")

        db.session.commit()

        out_path = (
            Path(app.instance_path)
            / f"temp_passwords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        out_path.write_text("\n".join(lines), encoding="utf-8")

        print(f"Готово: {len(ready)} сотрудников получили временный пароль.")
        print(f"Список сохранён в файле: {out_path}")
        print("Передайте пароли лично и удалите файл после этого.")


if __name__ == "__main__":
    main()
