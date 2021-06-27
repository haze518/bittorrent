import struct
from dataclasses import dataclass

import messages

@dataclass
class Handshake:
    info_hash: bytes
    peer_id: bytes


class HandshakeTranslator:

    _pstrlen = 19  # длина идентификатора протокола
    _pstr = b'BitTorrent protocol'  # идентификатор протокола == BitTorrent protocol

    @classmethod
    def serialize(cls, info_hash: bytes, peer_id: bytes) -> bytes:
        return struct.pack(
            '>B19s8x20s20s',  # len(BitTorrent protocol), BitTorrent protocol, reserved bytes, info_hash, peer_id
            cls._pstrlen,
            cls._pstr,
            info_hash,
            peer_id,
        )

    @classmethod
    def deserialize(cls, message: bytes):
        info_hash, peer_id = struct.unpack('>B19s8x20s20s', message)[2:]
        return Handshake(info_hash, peer_id)


class RequestTranslator:

    @classmethod
    def serialize(self, index: int, begin: int, length: int):
        return struct.pack(
            '>IbIII',
            13,  # длина указанная в протоколе
            messages.MessageID.Request.value,
            index,
            begin,
            length,
        )
