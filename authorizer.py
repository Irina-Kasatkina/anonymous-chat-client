# coding=utf-8

"""Функции для авторизации."""

import asyncio
import json
from asyncio.streams import StreamReader, StreamWriter
from contextlib import suppress

from common_utilities import open_connection, submit_message
from exceptions import InvalidToken


async def authorize(reader: StreamReader, writer: StreamWriter, token: str) -> str:
    """Авторизует пользователя в чате."""
    host_response = await reader.readline()
    await submit_message(writer, token)

    with suppress(json.decoder.JSONDecodeError):
        host_response = await reader.readline()
        account_parameters = json.loads(host_response)
        if account_parameters:
            return account_parameters['nickname']
    return ''


async def check_token(host: str, port: int, token: str, queue: asyncio.Queue) -> None:
    """Проверяет корректность токена."""
    if not token:
        raise InvalidToken('Токен не указан', 'Укажите токен, без него работа с чатом невозможна')

    nickname = ''
    async with open_connection(host, port) as (reader, writer):
        nickname = await authorize(reader, writer, token)

    if nickname:
        queue.put_nowait(f'Выполнена авторизация. Пользователь {nickname}.\n')
        return

    raise InvalidToken('Неверный токен', 'Проверьте токен, сервер его не узнал')
