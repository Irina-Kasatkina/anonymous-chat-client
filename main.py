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

import aiofiles
import configargparse
from dotenv import load_dotenv

import defaults


DELAY_PER_SECONDS = 1
SLEEP_INTERVAL = 1 / 120


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
        '-hs',
        '--host-for-sender',
        type=str,
        env_var='HOST_FOR_SENDER',
        default=defaults.HOST_FOR_SENDER,
        help='Хост для отправки сообщений в чат'
    )
    parser.add(
        '-ps',
        '--port-for-sender',
        type=int,
        env_var='PORT_FOR_SENDER',
        default=defaults.PORT_FOR_SENDER,
        help='Порт для отправки сообщений в чат'
    )     
    return parser.parse_args()


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""

    args = read_parse_args()

    messages_queue = asyncio.Queue()
    with suppress(FileNotFoundError):
        with open(args.history_filepath, 'r', encoding='UTF8') as file_handler:
            messages = file_handler.read().rstrip()
        messages_queue.put_nowait(messages)

    file_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(args.host_for_listener, args.port_for_listener, messages_queue, file_queue),
        save_messages(args.history_filepath, file_queue),
        send_msgs(args.host_for_sender, args.port_for_sender, sending_queue, messages_queue)
    )


async def read_msgs(host: str, port: int, queue: asyncio.Queue, file_queue: asyncio.Queue) -> None:
    """Читает сообщения из чата и записывает их в две очереди."""

    while True:
        async with open_connection(host, port) as (reader, _):
            while True:
                try:
                    chat_message = await asyncio.wait_for(reader.readline(), timeout=10.0)
                    message = chat_message.decode().rstrip()
                    queue.put_nowait(message)
                    file_queue.put_nowait(message)
                    await asyncio.sleep(SLEEP_INTERVAL)
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

            await asyncio.sleep(DELAY_PER_SECONDS)
            continue

        finally:
            if writer:
                writer.close()
                await writer.wait_closed()


def handle_keyboard_interrupt(signal, frame):
    """Обрабатывает прерывание работы программы с клавиатуры."""
    exit(0)


async def save_messages(filepath: str, queue: asyncio.Queue) -> None:
    """Записывает сообщения в текстовый файл, находящийся по указанному пути."""

    while True:
        msg = await queue.get()
        async with aiofiles.open(filepath, 'a', encoding='UTF8') as file_handler:
            await file_handler.write(f'{msg}\n')
        await asyncio.sleep(SLEEP_INTERVAL)


async def send_msgs(host: str, port: int, queue: asyncio.Queue, messages_queue: asyncio.Queue) -> None:
    """Записывает ввод пользователя в список входящих сообщений."""

    while True:
        message = await queue.get()
        messages_queue.put_nowait(f'Пользователь написал: {message}')
        await asyncio.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    print(asyncio.__file__)
    with suppress(gui.TkAppClosed, KeyboardInterrupt):
        asyncio.run(main())
