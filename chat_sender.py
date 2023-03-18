# coding=utf-8

"""Функции для отправки сообщений в чат."""

import asyncio

from authorizer import authorize
from connections import close_connection, open_connection, submit_message
from gui import SendingConnectionStateChanged


SENDER_SLEEP_INTERVAL = 1 / 120


async def send_messages(
    host: str,
    port: int,
    token: str,
    queue: asyncio.Queue,
    status_update_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue
) -> None:
    """Отправляет на сервер сообщения из очереди."""
    reader, writer = await open_connection(host, port, status_update_queue, SendingConnectionStateChanged)
    try:
        status_update_queue.put_nowait(SendingConnectionStateChanged.ESTABLISHED)
        successful_authorization = await authorize(reader, writer, token)
        if not successful_authorization:
            watchdog_queue.put_nowait('Authorization error')
            return

        status_update_queue.put_nowait(SendingConnectionStateChanged.ESTABLISHED)
        await reader.readline()
        while True:
            status_update_queue.put_nowait(SendingConnectionStateChanged.ESTABLISHED)
            message = await queue.get()
            await submit_message(writer, message)

            watchdog_queue.put_nowait('Message sent')
            await asyncio.sleep(SENDER_SLEEP_INTERVAL)
    except asyncio.CancelledError:
        raise
    finally:
        await close_connection(writer, status_update_queue, SendingConnectionStateChanged)
