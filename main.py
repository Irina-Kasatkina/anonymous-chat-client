# coding=utf-8

"""Запуск интерфейса пользователя чата."""

import asyncio
import gui
import time
from contextlib import suppress


async def generate_msgs(queue: asyncio.Queue) -> None:
    """Генерирует сообщения."""

    while True:
        queue.put_nowait(f'Ping {int(time.time())}')
        await asyncio.sleep(1)


async def main() -> None:
    """Инициализирует переменные и запускает программу ."""

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    with suppress(gui.TkAppClosed, KeyboardInterrupt):
        await asyncio.gather(
            gui.draw(messages_queue, sending_queue, status_updates_queue),
            generate_msgs(messages_queue)
        )


if __name__ == '__main__':
    asyncio.run(main())
