# coding=utf-8

"""Запуск графического интерфейса регистрации нового пользователя в чате."""

import asyncio
import json
import tkinter as tk
from asyncio.streams import StreamReader, StreamWriter
from contextlib import suppress
from tkinter.scrolledtext import ScrolledText

import aiofiles
import anyio

import defaults
from args_parser import read_parse_args
from connections import close_connection, open_connection, sanitize_text
from exceptions import RegistrationError
from gui import SendingConnectionStateChanged, TkAppClosed, update_tk


def start_register(address_field: tk.Entry, nickname_field: tk.Entry, events_queue: asyncio.Queue) -> None:
    """Посылает сообщение о начале регистрации."""
    server_address = address_field.get()
    nickname = nickname_field.get()
    events_queue.put_nowait((server_address, nickname))


async def register(reader: StreamReader, writer: StreamWriter, nickname: str) -> dict:
    """Регистрирует нового пользователя в чате."""
    await reader.readline()
    writer.write(f'\n'.encode())
    await writer.drain()

    await reader.readline()
    writer.write(f'{sanitize_text(nickname)}\n'.encode())
    await writer.drain()

    host_response = await reader.readline()
    with suppress(json.decoder.JSONDecodeError):
        account_parameters = json.loads(host_response)
        if account_parameters:
            return account_parameters

    raise RegistrationError()


async def display_log(log_queue: asyncio.Queue, log_text_area: ScrolledText) -> None:
    """Показывает сообщения о ходе регистрации в GUI."""
    while True:
        message = await log_queue.get()
        if isinstance(message, str):
            message, level = message, 'INFO'
        else:
            message, level = message
        log_text_area.configure(state='normal')
        log_text_area.insert(tk.END, message + '\n', level)
        log_text_area.configure(state='disabled')
        log_text_area.yview(tk.END)


async def write_token_to_file(account_parameters: dict) -> bool:
    """Записывает параметры пользователя в файл."""
    try:
        async with aiofiles.open(defaults.USER_TOKEN_FILE, 'w', encoding='UTF8') as json_file:
            await json_file.write(json.dumps(account_parameters))
            return True
    except (PermissionError, IsADirectoryError):
        return False


async def watch_register(events_queue: asyncio.Queue, log_queue: asyncio.Queue, result_token_field: tk.Entry) -> None:
    """Проверяет пользовательский ввод и регистрирует пользователя."""
    while True:
        server_address, nickname = await events_queue.get()
        nickname = nickname.strip()
        try:
            host, port = server_address.split(':')
            port = int(port)
        except ValueError:
            await log_queue.put(('Укажите адрес сервера в формате host:port', 'ERROR'))
            continue
        if not nickname:
            await log_queue.put(('Укажите свой ник.', 'ERROR'))
            continue
        await log_queue.put(f'Начинается процесс регистрации нового пользователя в чате. {nickname} на {host}:{port}')
        dummy_queue = asyncio.Queue()
        reader, writer = await open_connection(host, port, dummy_queue, SendingConnectionStateChanged)
        try:
            account_parameters = await register(reader, writer, nickname)
        except (ConnectionError, UnicodeDecodeError, RegistrationError):
            await log_queue.put(('Регистрация закончилась неудачно. Попробуйте позднее.', 'ERROR'))
        else:
            result_token_field.delete(0, tk.END)
            result_token_field.insert(0, account_parameters['account_hash'])
            to_file_status = await write_token_to_file(account_parameters)
            if to_file_status:
                await log_queue.put(
                    (f'Успешная регистрация. Токен сохранён в файле {defaults.USER_TOKEN_FILE}', 'SUCCESS')
                )
            else:
                await log_queue.put(
                    ('Успешная регистрация. Сохраните токен для его использования при запуске чата.', 'SUCCESS')
                )
        finally:
            await close_connection(writer, dummy_queue, SendingConnectionStateChanged)


async def draw(host: str, port: int, events_queue: asyncio.Queue, log_queue: asyncio.Queue) -> None:
    """Рисует интерфейс регистрации пользователя."""
    root = tk.Tk()
    root.title('Регистрация пользователя в чате')

    root_frame = tk.Frame()
    root_frame.pack(fill='both', expand=True)

    address_frame = tk.Frame(root_frame)
    address_label = tk.Label(address_frame, text='Адрес сервера: ', width=20, pady=10)
    address_field = tk.Entry(address_frame, width=40)
    address_field.delete(0, tk.END)
    address_field.insert(0, f'{host}:{port}')
    address_frame.pack()
    address_label.pack(side=tk.LEFT)
    address_field.pack(expand=1)

    nickname_frame = tk.Frame(root_frame)
    nickname_label = tk.Label(nickname_frame, text='Введите ник: ', width=20, pady=10)
    nickname_field = tk.Entry(nickname_frame, width=40)
    nickname_frame.pack()
    nickname_label.pack(side=tk.LEFT)
    nickname_field.pack(expand=1)

    reg_button_frame = tk.Frame(root_frame)
    reg_button = tk.Button(reg_button_frame, text='Зарегистрироваться')
    reg_button_frame.pack()
    reg_button.pack()

    result_token_frame = tk.Frame(root_frame)
    result_token_label = tk.Label(result_token_frame, text='Ваш токен: ', width=20, pady=10)
    result_token_field = tk.Entry(result_token_frame, width=40)
    result_token_frame.pack()
    result_token_label.pack(side=tk.LEFT)
    result_token_field.pack(expand=1)

    log_frame = tk.Frame(root_frame)
    log_text_area = ScrolledText(log_frame, state='disabled', height=12)
    log_text_area.configure(font='TkFixedFont')
    log_text_area.tag_configure('INFO', foreground='gray')
    log_text_area.tag_configure('ERROR', font='bold', foreground='red')
    log_text_area.tag_configure('SUCCESS', font='bold', foreground='green')
    log_frame.pack()
    log_text_area.pack(expand=1)

    reg_button['command'] = lambda: start_register(address_field, nickname_field, events_queue)

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(update_tk, root)
        task_group.start_soon(watch_register, events_queue, log_queue, result_token_field)
        task_group.start_soon(display_log, log_queue, log_text_area)


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""
    args = read_parse_args()

    events_queue = asyncio.Queue()
    log_queue = asyncio.Queue()

    await draw(args.sender_host, args.sender_port, events_queue, log_queue)


if __name__ == '__main__':
    with suppress(TkAppClosed, KeyboardInterrupt):
        asyncio.run(main())
