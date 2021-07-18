from __future__ import annotations
import socket
import struct
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import p2p
import client

HEADER_SIZE = 4


@dataclass
class Message:
    id: int
    payload: bytes


class MessageID(Enum):
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    Bitfield = 5
    Request = 6
    Piece = 7
    Cancel = 8


def handle_message(message: Message, client: client.Client, block: p2p.Block):
    if message.id == MessageID.Choke.value:
        _handle_choke(client)
    elif message.id == MessageID.Unchoke.value:
        _handle_unchoke(client)
    elif message.id == MessageID.Have.value:
        _handle_have(client, message)
    elif message.id == MessageID.Piece.value:
        _handle_piece(client, message, block)


def _handle_choke(cli: client.Client) -> None:
    logging.info(f'handle choke for client {cli.conn.getsockname()[0]}')
    cli.conn.close()


def _handle_unchoke(cli: client.Client) -> None:
    logging.info(f'handle UNchoke for client {cli.conn.getsockname()[0]}')
    cli.chocked = False


def _handle_have(cli: client.Client, message: Message):
    logging.info(f'handle have for client {cli.conn.getsockname()[0]}')
    if len(message.payload) != 4:
        logging.info(f'Expected payload of length 4, got: {len(message.payload)}')
    else:
        index = struct.unpack('>I', message.payload)[0]
        cli.bitfield[index] = 1


def _handle_piece(cli: client.Client, message: Message, block: p2p.Block):
    logging.info(f'handle piece for client {cli.conn.getsockname()[0]}')
    if len(message.payload) < 8:
        logging.info(f'Incorrect piece payload size: {len(message.payload)}')
        return None
    index, begin, payload = struct.unpack('>II' + '%ss' % len(message.payload[8:]), message.payload)
    if index != block.index or begin != block.begin:
        logging.info(
            'Incorrect block response: index: %s != block_index: %s or begin: %s != block_begin: %s' %
            (index, block.index, begin, block.begin)
        )
    else:
        block.data = payload


def read_message(sock: socket.socket) -> Optional[Message]:
    try:
        length = sock.recv(HEADER_SIZE)
        if len(length) != 4:
            return None
        length_unpacked = struct.unpack('>I', length)[0]
        if length_unpacked == 0:
            return 'keep_alive'  # keep_alive
        response = sock.recv(length_unpacked)
        id, payload = struct.unpack('>b' + str(len(response)-1) + 's', response)
        return Message(id=id, payload=payload)
    except socket.timeout:
        logging.info('an error occured while load message')
