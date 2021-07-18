from __future__ import annotations
import logging
import socket
import struct
import bitstring
from dataclasses import dataclass
from typing import Optional

import messages
import translator
import tracker

HANDSHAKE_LEN = 68


@dataclass
class Client:
    info_hash: bytes
    peer_id: bytes
    bitfield: bitstring.BitArray
    conn: socket.socket
    chocked: bool


def load_client(peer: tracker.Peer, info_hash: bytes, peer_id: bytes) -> Optional[Client]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    logging.info(f'try to connect to client: {peer.ip}')
    try:
        sock.connect((peer.ip, peer.port))
    except (socket.timeout, ConnectionRefusedError, OSError):
        return None
    for _ in range(5):
        if not _complete_handshake(info_hash, peer_id, sock):
            continue
        try:
            message = messages.read_message(sock)
        except socket.timeout:
            logging.info(f"can't load client")
            sock.close()
            return None
        if message:
            logging.info(f'success connect to {peer.ip}')
            return Client(
                info_hash=info_hash,
                peer_id=peer_id,
                bitfield=bitstring.BitArray(message.payload),
                conn=sock,
                chocked=False,
            )


def _complete_handshake(info_hash: bytes, peer_id: bytes, socket: socket.socket) -> bool:
    socket.send(translator.HandshakeTranslator.serialize(info_hash, peer_id))
    try:
        message = socket.recv(HANDSHAKE_LEN)
        return translator.HandshakeTranslator.deserialize(message).info_hash == info_hash
    except Exception:
        return False


def send_interested(socket: socket.socket) -> None:
    socket.send(struct.pack('>Ib', 1, messages.MessageID.Interested.value)) 


def send_unchoke(socket: socket.socket) -> None:
    socket.send(struct.pack('>Ib', 1, messages.MessageID.Unchoke.value)) 


def send_request(socket: socket.socket, index: int, begin: int, length: int):
    logging.info(f'Requesting block : {begin}, for piece: {index}, of length: {length}')
    socket.send(translator.RequestTranslator.serialize(index, begin, length))


def check_bitfield_index(bitfield: bitstring.BitArray, index: int):
    try:
        return bool(bitfield[index])
    except IndexError:
        return False
