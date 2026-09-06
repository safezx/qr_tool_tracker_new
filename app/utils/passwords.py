"""Генерация временных паролей для сотрудников."""

import secrets

# Без символов, которые легко перепутать на слух/при переписывании: 0/O, 1/I/L.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_temp_password(length=8):
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
