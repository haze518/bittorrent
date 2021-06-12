import bencodepy
import hashlib
from dataclasses import dataclass
from typing import List


@dataclass
class TorrentFile:
    announce: str
    info_hash: bytes
    piece_hashes: List[bytes]
    length: int
    piece_length: int
    name: str


def parse_torrent_file(path: str) -> TorrentFile:
    with open(path, 'rb') as file:
        data = file.read()
    decoded = bencodepy.decode(data)
    return TorrentFile(
        announce=decoded[b'announce'].decode('utf-8'),
        info_hash=_get_info_hash(decoded[b'info']),
        piece_hashes=_split_pieces(decoded[b'info'][b'pieces']),
        length=decoded[b'info'][b'length'],
        piece_length=decoded[b'info'][b'piece length'],
        name=decoded[b'info'][b'name'].decode('utf-8'),
    )


def _split_pieces(raw_pieces: bytes) -> List[bytes]:
    pieces = []
    offset = 0
    length = len(raw_pieces)
    while offset < length:
        pieces.append(raw_pieces[offset:offset + 20])
        offset += 20
    return pieces


def _get_info_hash(info: dict) -> bytes:
    return hashlib.sha1(bytearray(bencodepy.encode(info))).digest()
