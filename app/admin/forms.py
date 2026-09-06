from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, FloatField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

# Подсказки для поля "Категория" (поле остаётся обычным текстовым —
# так проще один раз показать варианты через <datalist>, не городя
# отдельную логику "выберите или введите своё").
DEFAULT_TOOL_CATEGORIES = [
    "Электроинструмент",
    "Ручной инструмент",
    "Измерительный",
    "Сварочное оборудование",
    "Пневматический",
    "Строительный",
    "Садовая техника",
    "Прочее",
]


class ToolForm(FlaskForm):
    name = StringField("Название инструмента", validators=[DataRequired(), Length(max=150)])
    category = StringField("Категория", validators=[Optional(), Length(max=50)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=2000)])
    location = StringField("Место хранения", validators=[Optional(), Length(max=100)])
    storage_place = StringField("Конкретное место (полка/ящик)", validators=[Optional(), Length(max=100)])
    serial_number = StringField("Серийный номер", validators=[Optional(), Length(max=50)])
    model = StringField("Модель", validators=[Optional(), Length(max=100)])
    manufacturer = StringField("Производитель", validators=[Optional(), Length(max=100)])
    price = FloatField("Цена, руб.", validators=[Optional(), NumberRange(min=0)])
    purchase_date = DateField("Дата приобретения", validators=[Optional()])
    warranty_until = DateField("Гарантия до", validators=[Optional()])


class EmployeeForm(FlaskForm):
    first_name = StringField("Имя", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Фамилия", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[Optional(), Length(max=100)])
    # Табельный номер теперь ещё и логин сотрудника — поэтому обязателен.
    employee_number = StringField(
        "Табельный номер (используется как логин)", validators=[DataRequired(), Length(max=20)]
    )
    department = StringField("Отдел", validators=[Optional(), Length(max=100)])
    phone = StringField("Телефон", validators=[Optional(), Length(max=20)])
    position = StringField("Должность", validators=[Optional(), Length(max=100)])
    is_active = BooleanField("Активен (может брать инструменты)", default=True)


class ReturnRequestForm(FlaskForm):
    """Возврат инструмента силами администратора (со страницы дашборда)."""

    condition_after = StringField(
        "Состояние после использования", validators=[Optional(), Length(max=255)]
    )
    notes = TextAreaField("Заметки администратора", validators=[Optional(), Length(max=500)])
