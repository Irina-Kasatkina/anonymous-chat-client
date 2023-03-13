# coding=utf-8

"""Запуск интерфейса пользователя чата."""

import argparse
import asyncio
import gui
import logging
import signal
import socket
import time
from asyncio.streams import StreamReader, StreamWriter
from contextlib import asynccontextmanager, suppress

import configargparse
from dotenv import load_dotenv

import defaults


DELAY_PER_SECONDS = 1


def read_parse_args() -> argparse.Namespace:
    """Принимает параметры из командной строки и файла .env."""
    
    load_dotenv()

    parser = configargparse.ArgParser(description='Асинхронный клиент для подключения к чату')
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
        read_msgs(args.host_for_listener, args.port_for_listener, messages_queue)
    )


async def read_msgs(host: str, port: int, queue: asyncio.Queue) -> None:
    """Читает сообщения из чата."""

    while True:
        async with open_connection(host, port) as (reader, _):
            while True:
                try:
                    chat_message = await asyncio.wait_for(reader.readline(), timeout=10.0)
                    message = chat_message.decode().rstrip()
                    queue.put_nowait(message)
                    await asyncio.sleep(1)
                except asyncio.exceptions.TimeoutError:
                    return


@asynccontextmanager
async def open_connection(host: str, port: int) -> (StreamReader, StreamWriter):
    """Устанавливает соединение с сервером по указанным хосту и порту."""
    
    connected = False
    while True:
        writer = None
        try:
            reader, writer = await asyncio.open_connection(host, port)
            signal.signal(signal.SIGINT, handle_keyboard_interrupt)
            connected = True            
            yield reader, writer
            break

        except (ConnectionRefusedError, ConnectionResetError, socket.gaierror, OSError):
            if connected:
                message = 'Произошёл обрыв соединения с сервером'
                logging.error(message)
                break

            message = 'Нет соединения с сервером'
            logging.warning(message)
            await asyncio.sleep(DELAY_PER_SECONDS)
            continue

        finally:
            if writer:
                writer.close()
                await writer.wait_closed()
            message = 'Соединение с сервером закрыто'
            logging.debug(message)


def handle_keyboard_interrupt(signal, frame):
    """Обрабатывает прерывание работы программы с клавиатуры."""

    logging.info('Работа программы была прервана с клавиатуры')
    exit(0)


if __name__ == '__main__':
    print(asyncio.__file__)
    with suppress(gui.TkAppClosed, KeyboardInterrupt):
        asyncio.run(main())
