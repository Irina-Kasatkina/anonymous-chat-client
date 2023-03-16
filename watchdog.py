# coding=utf-8

"""Отслеживание соединений с сервером."""

import asyncio
import logging
import time

import async_timeout


WATCHDOG_TIMEOUT = 10


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
watchdog_logger = logging.getLogger()


async def watch_for_connection(watchdog_queue: asyncio.Queue) -> None:
    """Отслеживает события соединения с чатом."""
    while True:
        try:
            async with async_timeout.timeout(WATCHDOG_TIMEOUT) as cm:
                event = await watchdog_queue.get()
        except asyncio.TimeoutError:
            watchdog_logger.info(f'[{int(time.time())}] {WATCHDOG_TIMEOUT}s timeout is elapsed')
        else:
            watchdog_logger.info(f'[{int(time.time())}] Connection is alive. {event}')
