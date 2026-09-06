from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class TakeToolForm(FlaskForm):
    purpose = TextAreaField(
        "Для каких работ нужен инструмент", validators=[Optional(), Length(max=500)]
    )
    return_date = DateField("Вернуть до", validators=[DataRequired()], format="%Y-%m-%d")


class ReturnToolForm(FlaskForm):
    condition_after = StringField(
        "Состояние после использования", validators=[Optional(), Length(max=255)]
    )
    notes = TextAreaField("Заметки", validators=[Optional(), Length(max=500)])
