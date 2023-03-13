# coding=utf-8

"""Запуск интерфейса пользователя чата."""

import argparse
import asyncio
import gui
import time
from contextlib import suppress

import configargparse
from dotenv import load_dotenv

import defaults


def read_parse_args() -> argparse.Namespace:
    """Принимает параметры из командной строки и файла .env."""
    
    load_dotenv()

    parser = configargparse.ArgParser(description='Асинхронный клиент для подключения к чату')
    parser.add(
        '-f',
        '--history-filepath',
        metavar='FILEPATH',
        type=str,
        env_var='HISTORY_FILEPATH',
        default=defaults.HISTORY_FILEPATH,
        help=f'Путь к файлу для сохранения истории переписки'
    )
    parser.add(
        '-hl',
        '--host-for-listener',
        type=str,
        env_var='HOST_FOR_LISTENER',
        default=defaults.HOST_FOR_LISTENER,
        help='Хост для прослушивания сообщений из чата'
    )
    parser.add(
        '-pl',
        '--port-for-listener',
        type=int,
        env_var='PORT_FOR_LISTENER',
        default=defaults.PORT_FOR_LISTENER,
        help='Порт для прослушивания сообщений из чата'
    )
    return parser.parse_args()


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""

    args = read_parse_args()
    print(args)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        generate_msgs(messages_queue)
    )


async def generate_msgs(queue: asyncio.Queue) -> None:
    """Генерирует сообщения."""

    while True:
        queue.put_nowait(f'Ping {int(time.time())}')
        await asyncio.sleep(1)


if __name__ == '__main__':
    with suppress(gui.TkAppClosed, KeyboardInterrupt):
        asyncio.run(main())
