# coding=utf-8

"""Функции для чтения сообщений чата."""

import asyncio

import constants
import gui
from common_utilities import open_connection


async def read_messages(
    host: str,
    port: int,
    queue: asyncio.Queue,
    file_queue: asyncio.Queue,
    status_update_queue: asyncio.Queue
) -> None:
    """Читает сообщения из чата и записывает их в очереди."""
    while True:
        async with open_connection(host, port, status_update_queue, gui.ReadConnectionStateChanged) as (reader, _):
            while True:
                try:
                    chat_message = await asyncio.wait_for(reader.readline(), timeout=10.0)
                    message = chat_message.decode().rstrip()
                    queue.put_nowait(message)
                    file_queue.put_nowait(message)
                    await asyncio.sleep(constants.SLEEP_INTERVAL)
                except asyncio.exceptions.TimeoutError:
                    return
        status_update_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
        await asyncio.sleep(constants.SLEEP_INTERVAL)
