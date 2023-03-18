# coding=utf-8

"""Запуск графического интерфейса пользователя чата."""

import asyncio
from contextlib import suppress
from tkinter import messagebox

import anyio

import gui
from args_parser import read_parse_args
from exceptions import InvalidToken
from history import put_history_to_queue, save_messages
from watchdog import handle_connection


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""
    args = read_parse_args()

    messages_queue = asyncio.Queue()
    file_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    put_history_to_queue(args.history_filepath, messages_queue)

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue)
        task_group.start_soon(save_messages, args.history_filepath, file_queue)
        task_group.start_soon(handle_connection, args.reader_host, args.reader_port, args.sender_host, args.sender_port,
                              args.token, messages_queue, sending_queue, file_queue, status_updates_queue,
                              watchdog_queue)


if __name__ == '__main__':
    try:
        with suppress(gui.TkAppClosed, KeyboardInterrupt):
            asyncio.run(main())
    except InvalidToken as ex:
        messagebox.showinfo(title=ex.title, message=ex.message)
