# coding=utf-8

"""Корутины, зависящие от соединения с сервером."""

import asyncio
import logging
import socket
import time

import anyio
import async_timeout

from authorizer import check_token
from chat_reader import read_messages
from chat_sender import send_messages
from exceptions import InvalidToken


PING_PONG_INTERVAL = 5
RECONNECTION_DELAY = 1
SERVER_SILENCE_TIMEOUT = 10


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
watchdog_logger = logging.getLogger()


async def handle_connection(
    reader_host: str,
    reader_port: int,
    sender_host: str,
    sender_port: int,
    token: str,
    messages_queue: asyncio.Queue,
    sending_queue: asyncio.Queue,
    file_queue: asyncio.Queue,
    status_updates_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue
) -> None:
    """Управляет группой корутин, которые зависят от успешного соединения с сервером."""
    while True:
        try:
            while True:
                try:
                    async with anyio.create_task_group() as task_group:
                        task_group.start_soon(check_token, sender_host, sender_port, token,
                                              messages_queue, status_updates_queue, watchdog_queue)
                        task_group.start_soon(read_messages, reader_host, reader_port,
                                              messages_queue, file_queue, status_updates_queue, watchdog_queue)
                        task_group.start_soon(send_messages, sender_host, sender_port, token,
                                              sending_queue, status_updates_queue, watchdog_queue)
                        task_group.start_soon(watch_for_connection, sending_queue, watchdog_queue)
                except (socket.gaierror, ConnectionError, UnicodeDecodeError):
                    watchdog_logger.warning('Connection error happened')
                    raise asyncio.CancelledError
                except anyio.ExceptionGroup as exception_group:
                    for exception in exception_group.exceptions:
                        if isinstance(exception, (socket.gaierror, ConnectionError)):
                            watchdog_logger.warning('Connection error happened')
                            raise asyncio.CancelledError
                    raise
        except asyncio.CancelledError:
            await asyncio.sleep(RECONNECTION_DELAY)


async def watch_for_connection(sending_queue: asyncio.Queue, watchdog_queue: asyncio.Queue) -> None:
    """Отслеживает события соединения с чатом."""
    while True:
        try:
            async with async_timeout.timeout(SERVER_SILENCE_TIMEOUT) as cm:
                event = await watchdog_queue.get()
                sending_queue.put_nowait('') # ping pong
                await asyncio.sleep(PING_PONG_INTERVAL)
            if cm.expired:
                raise ConnectionError
        except asyncio.TimeoutError:
            watchdog_logger.info(f'[{int(time.time())}] {SERVER_SILENCE_TIMEOUT}s timeout is elapsed')
            raise ConnectionError
        else:
            watchdog_logger.info(f'[{int(time.time())}] Connection is alive. {event}')
