# coding=utf-8

"""Собственные классы исключений проекта."""

from typing import Optional


class InvalidToken(Exception):
    def __init__(self, title: str, message: Optional[str] = '') -> None:
        self.title = title
        self.message = message
        super().__init__(title)


class RegistrationError(Exception):
    def __init__(self) -> None:
        self.title = 'Регистрация пользователя'
        self.message = 'Ошибка при регистрации, попробуйте позднее.'
        super().__init__()
