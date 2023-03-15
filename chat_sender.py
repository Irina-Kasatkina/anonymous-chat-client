# coding=utf-8

"""Функции для отправки сообщений в чат."""

import asyncio

import constants
from authorizer import authorize
from common_utilities import open_connection, submit_message
from exceptions import InvalidToken


async def send_messages(host: str, port: int, token: str, queue: asyncio.Queue) -> None:
    """Отправляет на сервер сообщения из очереди."""
    while True:
        message = await queue.get()        
        async with open_connection(host, port) as (reader, writer):
            successful_authorization = await authorize(reader, writer, token)
            if not successful_authorization:
                raise InvalidToken('Неверный токен', 'Проверьте токен, сервер его не узнал')

            host_response = await reader.readline()
            await submit_message(writer, message)

        await asyncio.sleep(constants.SLEEP_INTERVAL)
