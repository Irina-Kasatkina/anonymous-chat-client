# coding=utf-8

"""Функции, общие для модулей проекта."""

import asyncio
import socket
from asyncio.streams import StreamReader, StreamWriter
from typing import Type, TypeVar

import async_timeout

from gui import ReadConnectionStateChanged, SendingConnectionStateChanged


WAIT_CONNECTION_SLEEP_INTERVAL = 1


StateChangeEnum = TypeVar('StateChangeEnum', ReadConnectionStateChanged, SendingConnectionStateChanged)


async def open_connection(
    host: str,
    port: int,
    status_update_queue: asyncio.Queue,
    gui_state_class: Type[StateChangeEnum]
) -> (StreamReader, StreamWriter):
    """Устанавливает соединение с сервером по указанным хосту и порту."""
    status_update_queue.put_nowait(gui_state_class.INITIATED)
    try:
        async with async_timeout.timeout(WAIT_CONNECTION_SLEEP_INTERVAL):
            reader, writer = await asyncio.open_connection(host, port)
        status_update_queue.put_nowait(gui_state_class.ESTABLISHED)
        return reader, writer
    except (ConnectionRefusedError, ConnectionResetError, socket.gaierror, OSError):
        raise ConnectionError


def sanitize_text(text: str) -> str:
    """Удаляет из текста символы перевода строки и возврата каретки."""
    return text.replace('\n', '').replace('\r', '')


async def submit_message(writer: StreamWriter, message: str) -> None:
    """Отправляет сообщение в чат."""
    message = f'{sanitize_text(message)}\n\n'
    writer.write(message.encode())
    await writer.drain()
