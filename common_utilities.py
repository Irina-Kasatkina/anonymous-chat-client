# coding=utf-8

"""Функции, общие для модулей проекта."""

import asyncio
import signal
import socket
from asyncio.streams import StreamReader, StreamWriter
from contextlib import asynccontextmanager, suppress


DELAY_PER_SECONDS = 1


def handle_keyboard_interrupt(signal, frame):
    """Обрабатывает прерывание работы программы с клавиатуры."""
    exit(0)


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


def sanitize_text(text: str) -> str:
    """Удаляет из текста символы перевода строки и возврата каретки."""
    return text.replace('\n', '').replace('\r', '')


async def submit_message(writer, message) -> None:
    """Отправляет сообщение в чат."""
    message = f'{sanitize_text(message)}\n\n'
    writer.write(message.encode())
    await writer.drain()
