"""
Работа со временем — единообразно, только московское время.

В старой версии проекта часть кода использовала pytz + московское время,
а часть — datetime.utcnow(), что приводило к путанице и рассинхрону дат.

Здесь принято простое правило: приложение работает в одном часовом поясе
(Europe/Moscow) и НИГДЕ не хранит и не сравнивает время в UTC. Все datetime,
которые попадают в базу данных, — это "наивные" (без tzinfo) значения,
означающие московское время. Раз в приложении нет других часовых поясов,
конвертация не нужна, а naive datetime гораздо проще для сравнения и хранения
в SQLite, чем "aware" datetime (не будет ошибок вида "can't compare
offset-naive and offset-aware datetimes").

Если в будущем понадобится поддержка нескольких часовых поясов — правильным
решением будет хранить в БД UTC и конвертировать только при отображении,
но для одного предприятия в одном городе это неоправданно усложнило бы код.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def moscow_now():
    """Текущее московское время как наивный datetime (без tzinfo)."""
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def moscow_today():
    """Текущая дата по московскому времени."""
    return moscow_now().date()


def format_moscow(value, fmt="%d.%m.%Y %H:%M"):
    """Форматирование даты/времени для шаблонов. Пусто -> тире."""
    if not value:
        return "—"
    return value.strftime(fmt)
