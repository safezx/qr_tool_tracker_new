"""
Команды для управления приложением из терминала.

Отдельного экрана "добавить администратора" в веб-интерфейсе нет
намеренно — заводить новых администраторов должен тот, у кого есть доступ
к серверу, а не через веб-форму. Используйте:

    flask create-admin <логин> "<Имя Фамилия>"
    flask reset-admin-password <логин>
"""

import getpass

import click

from .extensions import db
from .models import Admin


def register_cli_commands(app):
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("full_name")
    def create_admin(username, full_name):
        """Создать нового администратора."""
        username = username.strip().lower()

        if Admin.query.filter_by(username=username).first():
            click.echo(f"Администратор '{username}' уже существует.")
            return

        password = _prompt_password()
        if password is None:
            return

        admin = Admin(username=username, full_name=full_name.strip())
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Администратор '{username}' создан.")

    @app.cli.command("reset-admin-password")
    @click.argument("username")
    def reset_admin_password(username):
        """Сбросить пароль администратора."""
        username = username.strip().lower()
        admin = Admin.query.filter_by(username=username).first()
        if not admin:
            click.echo(f"Администратор '{username}' не найден.")
            return

        password = _prompt_password()
        if password is None:
            return

        admin.set_password(password)
        db.session.commit()
        click.echo(f"Пароль администратора '{username}' обновлён.")


def _prompt_password():
    password = getpass.getpass("Пароль (мин. 8 символов): ")
    if len(password) < 8:
        click.echo("Пароль должен быть не короче 8 символов. Отменено.")
        return None

    confirm = getpass.getpass("Повторите пароль: ")
    if password != confirm:
        click.echo("Пароли не совпадают. Отменено.")
        return None

    return password
