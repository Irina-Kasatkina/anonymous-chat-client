# coding=utf-8

"""Функции для приёма аргументов командной строки и файла .env."""

import argparse
import json

import configargparse
from dotenv import load_dotenv
from contextlib import suppress

import defaults


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
        help='Токен пользователя чата'
    )
    parser.add(
        '-rh',
        '--reader-host',
        type=str,
        env_var='READER_HOST',
        default=defaults.READER_HOST,
        help='Хост для чтения сообщений из чата'
    )
    parser.add(
        '-rp',
        '--reader-port',
        type=int,
        env_var='READER_PORT',
        default=defaults.READER_PORT,
        help='Порт для чтения сообщений из чата'
    )
    parser.add(
        '-sh',
        '--sender-host',
        type=str,
        env_var='SENDER_HOST',
        default=defaults.SENDER_HOST,
        help='Хост для отправки сообщений в чат'
    )
    parser.add(
        '-sp',
        '--sender-port',
        type=int,
        env_var='SENDER_PORT',
        default=defaults.SENDER_PORT,
        help='Порт для отправки сообщений в чат'
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
