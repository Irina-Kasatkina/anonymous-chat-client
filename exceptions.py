# coding=utf-8

"""Собственные классы исключений проекта."""

from typing import Optional


class InvalidToken(Exception):
    def __init__(self, title: str, message: Optional[str] = '') -> None:
        self.title = title
        self.message = message
        super().__init__(title)
