import struct
import logging
from dataclasses import dataclass
from enum import Enum

import p2p
import client


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
    if message.id == MessageID.Choke:
        _handle_choke(client)
    elif message.id == MessageID.Unchoke:
        _handle_unchoke(client)
    elif message.id == MessageID.Have:
        _handle_have(client)
    elif message.id == MessageID.Piece:
        _handle_piece(message, block)


def _handle_choke(client: client.Client) -> None:
    client.conn.close()


def _handle_unchoke(client: client.Client) -> None:
    client.chocked = False


def _handle_have(message: Message, client: client.Client):
    if len(message.payload) != 4:
        logging.info(f'Expected payload of length 4, got: {len(message.payload)}')
    else:
        index = struct.unpack('>I', message.payload)[0]
        client.bitfield[index] = 1


def _handle_piece(message: Message, block: p2p.Block):
    if len(message.payload) < 8:
        logging.info(f'Incorrect piece payload size: {len(message.payload)}')
        return None
    index, begin, payload = struct.unpack('>II' + '%ss' % len(message[8:]), message)
    if index != block.index or begin != block.begin:
        logging.info(
            'Incorrect block response: index: %s != block_index: %s or begin: %s != block_begin: %s' %
            (index, block.index, begin, block.begin)
        )
    else:
        block.data = payload


def read_message(client: client.Client) -> Message:
    header_size = 4
    length = client.conn.recv(header_size)
    if not length:
        return None  # keep_alive
    length_unpacked = struct.unpack('>I', length)[0]
    response = client.conn.recv(length_unpacked)
    id, payload = struct.unpack('>b' + str(len(response)-1) + 's', response)
    return Message(id=id, payload=payload)
