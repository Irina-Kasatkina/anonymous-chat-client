# coding=utf-8

"""Отслеживание соединений с сервером."""

import asyncio
import logging
import time


WATCHDOG_SLEEP_INTERVAL = 1 / 120


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
watchdog_logger = logging.getLogger()


async def watch_for_connection(watchdog_queue: asyncio.Queue) -> None:
    """Отслеживает события соединения с чатом."""
    while True:
        event = await watchdog_queue.get()
        watchdog_logger.info(f'[{int(time.time())}] Connection is alive. {event}')
        await asyncio.sleep(WATCHDOG_SLEEP_INTERVAL)
