# coding=utf-8

"""Функции для работы с файлом сохранения истории сообщений."""

import asyncio
from contextlib import suppress

import aiofiles

import constants


def put_history_to_queue(filepath: str, queue: asyncio.Queue) -> None:
    """Создаёт очередь сообщений и помещает в неё сообщения из файла."""
    with suppress(FileNotFoundError):
        with open(filepath, 'r', encoding='UTF8') as file_handler:
            messages = file_handler.read()
        queue.put_nowait(messages)


async def save_messages(filepath: str, queue: asyncio.Queue) -> None:
    """Записывает сообщения в текстовый файл, находящийся по указанному пути."""
    while True:
        msg = await queue.get()
        async with aiofiles.open(filepath, 'a', encoding='UTF8') as file_handler:
            await file_handler.write(f'{msg}\n')
        await asyncio.sleep(constants.SLEEP_INTERVAL)
