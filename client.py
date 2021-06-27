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
    sock.connect((peer.ip. peer.port))
    if _complete_handshake(info_hash, peer_id, sock):
        message = messages.read_message(sock)
        if message:
            return Client(
                info_hash=info_hash,
                peer_id=peer_id,
                bitfield=bitstring.BitArray(message.payload),
                conn=sock,
                chocked=True,
            )


def _complete_handshake(info_hash: bytes, peer_id: bytes, socket: socket.socket) -> bool:
    socket.send(translator.HandshakeTranslator.serialize(info_hash, peer_id))
    message = socket.recv(HANDSHAKE_LEN)
    try:
        return translator.HandshakeTranslator.deserialize(message).info_hash == info_hash
    except Exception:
        return False


def send_interested(socket: socket.socket) -> None:
    socket.send(struct.pack('>I', messages.MessageID.Interested.value)[0]) 


def send_unchoke(socket: socket.socket) -> None:
    socket.send(struct.pack('>I', messages.MessageID.Unchoke.value)[0]) 


def send_request(socket: socket.socket, index: int, begin: int, length: int):
    socket.send(translator.RequestTranslator.serialize(index, begin, length))


def check_bitfield_index(bitfield: bitstring.BitArray, index: int):
    try:
        return bool(bitfield[index])
    except IndexError:
        return False
