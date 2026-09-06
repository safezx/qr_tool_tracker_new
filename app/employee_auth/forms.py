from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, EqualTo, Length


class EmployeeLoginForm(FlaskForm):
    employee_number = StringField("Табельный номер", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Текущий пароль", validators=[DataRequired()])
    new_password = PasswordField("Новый пароль", validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField(
        "Повторите новый пароль",
        validators=[DataRequired(), EqualTo("new_password", message="Пароли не совпадают")],
    )
