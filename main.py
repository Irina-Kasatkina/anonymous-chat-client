# coding=utf-8

"""Запуск интерфейса пользователя чата."""

import argparse
import asyncio
import gui
import json
import logging
import signal
import socket
import time
from asyncio.streams import StreamReader, StreamWriter
from contextlib import asynccontextmanager, suppress
from tkinter import messagebox
from typing import Optional

import aiofiles
import configargparse
from dotenv import load_dotenv

import defaults


DELAY_PER_SECONDS = 1
SLEEP_INTERVAL = 1 / 120


class InvalidToken(Exception):
    def __init__(self, title: str, message: Optional[str] = '') -> None:
        self.title = title
        self.message = message
        super().__init__(title)


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""
    args = read_parse_args()

    messages_queue = create_messages_queue(args.history_filepath)
    file_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        check_token(args.host_for_sender, args.port_for_sender, args.token, messages_queue),
        read_messages(args.host_for_listener, args.port_for_listener, messages_queue, file_queue),
        save_messages(args.history_filepath, file_queue),
        send_messages(args.host_for_sender, args.port_for_sender, args.token, sending_queue)
    )


def read_parse_args() -> argparse.Namespace:
    """Принимает параметры из командной строки и файла .env."""
    load_dotenv()

    parser = configargparse.ArgParser(description='Асинхронный клиент для подключения к чату')
    parser.add(
        '-t',
        '--token',
        type=str,
        env_var='USER_TOKEN',
        default='',
        help='Токен для отправки сообщений в чат'
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
    args = parser.parse_args()
    if not args.token:
        args.token = read_token_from_file()
    return args


def read_token_from_file() -> str:
    """Получает токен из указанного файла с именем, записанным в defaults.USER_TOKEN_FILE."""
    token = ''
    with suppress(FileNotFoundError):
        with open(defaults.USER_TOKEN_FILE, 'r', encoding='UTF8') as token_file:
            token = json.load(token_file).get('account_hash', '')
    return token


def create_messages_queue(filepath: str) -> asyncio.Queue:
    """Создаёт очередь сообщений и помещает в неё сообщения из файла."""
    queue = asyncio.Queue()
    with suppress(FileNotFoundError):
        with open(filepath, 'r', encoding='UTF8') as file_handler:
            messages = file_handler.read()
        queue.put_nowait(messages)
    return queue


async def read_messages(host: str, port: int, queue: asyncio.Queue, file_queue: asyncio.Queue) -> None:
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


async def check_token(host: str, port: int, token: str, queue: asyncio.Queue) -> None:
    """Проверяет корректность токена."""
    if not token:
        raise InvalidToken('Токен не указан', 'Укажите токен, без него работа с чатом невозможна')

    nickname = ''
    async with open_connection(host, port) as (reader, writer):
        nickname = await authorize(reader, writer, token)

    if nickname:
        queue.put_nowait(f'Выполнена авторизация. Пользователь {nickname}.\n')
        return

    raise InvalidToken('Неверный токен', 'Проверьте токен, сервер его не узнал')


async def authorize(reader: StreamReader, writer: StreamWriter, token: str) -> str:
    host_response = await reader.readline()
    await submit_message(writer, token)

    with suppress(json.decoder.JSONDecodeError):
        host_response = await reader.readline()
        account_parameters = json.loads(host_response)
        if account_parameters:
            return account_parameters['nickname']
    return ''


async def submit_message(writer, message) -> None:
    """Отправляет сообщение в чат."""
    message = f'{sanitize_text(message)}\n\n'
    writer.write(message.encode())
    await writer.drain()


def sanitize_text(text: str) -> str:
    """Удаляет из текста символы перевода строки и возврата каретки."""
    return text.replace('\n', '').replace('\r', '')


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

        await asyncio.sleep(SLEEP_INTERVAL)


if __name__ == '__main__':
    try:
        with suppress(gui.TkAppClosed, KeyboardInterrupt):
            asyncio.run(main())
    except InvalidToken as ex:
        messagebox.showinfo(title=ex.title, message=ex.message)
