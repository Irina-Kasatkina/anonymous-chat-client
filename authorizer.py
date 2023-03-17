# coding=utf-8

"""Функции для авторизации."""

import asyncio
import json
from asyncio.streams import StreamReader, StreamWriter
from contextlib import suppress

from connections import open_connection, submit_message
from exceptions import InvalidToken
from gui import NicknameReceived, SendingConnectionStateChanged


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


async def check_token(
    host: str,
    port: int,
    token: str,
    queue: asyncio.Queue,
    status_update_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue
) -> None:
    """Проверяет корректность токена."""
    if not token:
        raise InvalidToken('Токен не указан', 'Укажите токен, без него работа с чатом невозможна')

    nickname = ''
    watchdog_queue.put_nowait('Prompt before auth')
    reader, writer = await open_connection(host, port, status_update_queue, SendingConnectionStateChanged)
    try:
        nickname = await authorize(reader, writer, token)
    except asyncio.CancelledError:
        raise
    finally:
        writer.close()
        await writer.wait_closed()

    if nickname:
        queue.put_nowait(f'Выполнена авторизация. Пользователь {nickname}.')
        status_update_queue.put_nowait(NicknameReceived(nickname))
        watchdog_queue.put_nowait('Authorization done')
        return

    raise InvalidToken('Неверный токен', 'Проверьте токен, сервер его не узнал')
