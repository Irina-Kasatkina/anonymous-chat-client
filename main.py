# coding=utf-8

"""Запуск интерфейса пользователя чата."""

import asyncio
import gui
from contextlib import suppress


def main() -> None:
    """Инициализирует переменные и запускает программу ."""

    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    with suppress(gui.TkAppClosed, KeyboardInterrupt):
        loop.run_until_complete(gui.draw(messages_queue, sending_queue, status_updates_queue))


if __name__ == '__main__':
    main()
