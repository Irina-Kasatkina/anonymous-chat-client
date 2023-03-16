# coding=utf-8

"""Запуск интерфейса пользователя чата."""

import asyncio
from contextlib import suppress
from tkinter import messagebox

import gui
from args_parser import read_parse_args
from authorizer import check_token
from chat_reader import read_messages
from chat_sender import send_messages
from exceptions import InvalidToken
from history import put_history_to_queue, save_messages


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""
    args = read_parse_args()

    messages_queue = asyncio.Queue()
    file_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    put_history_to_queue(args.history_filepath, messages_queue)

    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        check_token(args.sender_host, args.sender_port, args.token, messages_queue, status_updates_queue),
        read_messages(args.reader_host, args.reader_port, messages_queue, file_queue, status_updates_queue),
        save_messages(args.history_filepath, file_queue),
        send_messages(args.sender_host, args.sender_port, args.token, sending_queue, status_updates_queue)
    )


if __name__ == '__main__':
    try:
        with suppress(gui.TkAppClosed, KeyboardInterrupt):
            asyncio.run(main())
    except InvalidToken as ex:
        messagebox.showinfo(title=ex.title, message=ex.message)
