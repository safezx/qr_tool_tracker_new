"""
Разовый перенос данных из старой версии проекта (SOIVM/projectArchive/qr_tool_tracker)
в новую схему БД.

Запуск (из корня нового проекта, с активированным venv):

    python scripts/migrate_old_data.py "путь\\к\\старому\\instance\\tool_tracker.db"

Инструменты и сотрудники переносятся без дублей (по QR-коду / табельному
номеру / email), поэтому скрипт можно перезапускать безопасно. Заявки же
создаются заново при каждом запуске — предполагается, что скрипт
выполняется один раз на чистую базу данных.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Employee, Tool, ToolRequest  # noqa: E402


def parse_datetime(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    print(f"  Не удалось разобрать дату/время: {value!r}")
    return None


def parse_date(value):
    dt = parse_datetime(value)
    return dt.date() if dt else None


def migrate(old_db_path):
    conn = sqlite3.connect(old_db_path)
    conn.row_factory = sqlite3.Row

    app = create_app()
    with app.app_context():
        employee_map = _migrate_employees(conn)
        tool_map = _migrate_tools(conn)
        _migrate_requests(conn, employee_map, tool_map)

    conn.close()
    print("Готово.")


def _migrate_employees(conn):
    mapping = {}
    rows = conn.execute("SELECT * FROM users").fetchall()

    for row in rows:
        existing = None
        if row["employee_id"]:
            existing = Employee.query.filter_by(employee_number=row["employee_id"]).first()
        if not existing and row["email"]:
            existing = Employee.query.filter_by(email=row["email"]).first()

        if existing:
            mapping[row["id"]] = existing.id
            continue

        employee = Employee(
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            employee_number=row["employee_id"],
            department=row["department"],
            phone=row["phone"] if "phone" in row.keys() else None,
            position=row["position"] if "position" in row.keys() else None,
            is_active=bool(row["is_active"]) if row["is_active"] is not None else True,
        )
        db.session.add(employee)
        db.session.flush()
        mapping[row["id"]] = employee.id

    db.session.commit()
    print(f"Сотрудников перенесено: {len(mapping)}")
    return mapping


def _migrate_tools(conn):
    mapping = {}
    rows = conn.execute("SELECT * FROM tools").fetchall()

    for row in rows:
        qr_code = row["qr_code_identifier"]
        existing = Tool.query.filter_by(qr_code=qr_code).first()
        if existing:
            mapping[row["id"]] = existing.id
            continue

        tool = Tool(
            name=row["name"],
            description=row["description"],
            category=row["category"],
            qr_code=qr_code,
            location=row["location"],
            storage_place=row["storage_place"],
            is_available=bool(row["is_available"]),
            serial_number=row["serial_number"],
            model=row["model"] if "model" in row.keys() else None,
            manufacturer=row["manufacturer"] if "manufacturer" in row.keys() else None,
            price=row["price"] if "price" in row.keys() else None,
            purchase_date=parse_date(row["purchase_date"]) if "purchase_date" in row.keys() else None,
            warranty_until=parse_date(row["warranty_until"]) if "warranty_until" in row.keys() else None,
        )
        db.session.add(tool)
        db.session.flush()
        mapping[row["id"]] = tool.id

    db.session.commit()
    print(f"Инструментов перенесено: {len(mapping)}")
    return mapping


def _migrate_requests(conn, employee_map, tool_map):
    rows = conn.execute("SELECT * FROM requests").fetchall()
    count = 0

    for row in rows:
        employee_id = employee_map.get(row["user_id"])
        tool_id = tool_map.get(row["tool_id"])
        if not employee_id or not tool_id:
            print(f"  Пропущена заявка #{row['id']} — не найден сотрудник или инструмент")
            continue

        request_time = parse_datetime(row["request_time"]) or datetime.utcnow()
        actual_return_time = parse_datetime(row["actual_return_time"])
        expected_return_dt = parse_datetime(row["expected_return_time"])
        expected_return_date = (
            expected_return_dt.date() if expected_return_dt else request_time.date()
        )

        status = row["status"]
        if status not in (ToolRequest.STATUS_APPROVED, ToolRequest.STATUS_RETURNED):
            # Старые статусы pending/rejected/overdue в реальности не
            # использовались — на всякий случай сводим к одному из двух.
            status = ToolRequest.STATUS_RETURNED if actual_return_time else ToolRequest.STATUS_APPROVED

        tool_request = ToolRequest(
            employee_id=employee_id,
            tool_id=tool_id,
            request_time=request_time,
            expected_return_date=expected_return_date,
            actual_return_time=actual_return_time,
            status=status,
            purpose=row["purpose"],
            condition_before=row["condition_before"] if "condition_before" in row.keys() else None,
            condition_after=row["condition_after"] if "condition_after" in row.keys() else None,
            admin_notes=row["admin_notes"],
        )
        db.session.add(tool_request)
        count += 1

    db.session.commit()
    print(f"Заявок перенесено: {count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python scripts/migrate_old_data.py <путь к старому tool_tracker.db>")
        sys.exit(1)

    old_path = sys.argv[1]
    if not Path(old_path).exists():
        print(f"Файл не найден: {old_path}")
        sys.exit(1)

    migrate(old_path)
