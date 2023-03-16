# coding=utf-8

"""Функции, общие для модулей проекта."""

import asyncio
import signal
import socket
from asyncio.streams import StreamReader, StreamWriter
from contextlib import asynccontextmanager, suppress
from typing import Type, TypeVar

import gui


DELAY_PER_SECONDS = 1


StateChangeEnum = TypeVar('StateChangeEnum', gui.ReadConnectionStateChanged, gui.SendingConnectionStateChanged)


@asynccontextmanager
async def open_connection(
    host: str,
    port: int,
    status_update_queue: asyncio.Queue,
    gui_state_class: Type[StateChangeEnum]
) -> (StreamReader, StreamWriter):
    """Устанавливает соединение с сервером по указанным хосту и порту."""
    status_update_queue.put_nowait(gui_state_class.INITIATED)
    connected = False
    while True:
        writer = None
        try:
            reader, writer = await asyncio.open_connection(host, port)
            status_update_queue.put_nowait(gui_state_class.ESTABLISHED)
            signal.signal(signal.SIGINT, handle_keyboard_interrupt)
            connected = True
            yield reader, writer
            break

        except (ConnectionRefusedError, ConnectionResetError, socket.gaierror, OSError):
            if connected:
                status_update_queue.put_nowait(gui_state_class.CLOSED)
                break

            await asyncio.sleep(DELAY_PER_SECONDS)
            continue

        finally:
            if writer:
                writer.close()
                status_update_queue.put_nowait(gui_state_class.CLOSED)
                await writer.wait_closed()


def handle_keyboard_interrupt(signal, frame):
    """Обрабатывает прерывание работы программы с клавиатуры."""
    exit(0)


def sanitize_text(text: str) -> str:
    """Удаляет из текста символы перевода строки и возврата каретки."""
    return text.replace('\n', '').replace('\r', '')


async def submit_message(writer, message) -> None:
    """Отправляет сообщение в чат."""
    message = f'{sanitize_text(message)}\n\n'
    writer.write(message.encode())
    await writer.drain()
