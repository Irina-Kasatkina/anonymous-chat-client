# coding=utf-8

"""Функции для чтения сообщений чата."""

import asyncio

from connections import close_connection, open_connection
from gui import ReadConnectionStateChanged

READER_SLEEP_INTERVAL = 1 / 120


async def read_messages(
    host: str,
    port: int,
    queue: asyncio.Queue,
    file_queue: asyncio.Queue,
    status_update_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue
) -> None:
    """Читает сообщения из чата и записывает их в очереди."""
    reader, writer = await open_connection(host, port, status_update_queue, ReadConnectionStateChanged)
    try:
        while True:
            chat_message = await reader.readline()
            message = chat_message.decode().rstrip()

            queue.put_nowait(message)
            file_queue.put_nowait(message)
            watchdog_queue.put_nowait('New message in chat')
            await asyncio.sleep(READER_SLEEP_INTERVAL)
    except asyncio.CancelledError:
        raise
    finally:
        await close_connection(writer, status_update_queue, ReadConnectionStateChanged)
