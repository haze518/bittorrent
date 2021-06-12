import bencodepy
import socket
import struct
import urllib.request
from dataclasses import dataclass
from typing import List
from urllib.parse import urlencode

from torrentfile import TorrentFile
from utils import gen_peer_id

PORT = 6881


@dataclass
class Peer:
    ip: str
    port: int


def get_peers(torrent_file: TorrentFile):
    data = _request_data_from_tracker(torrent_file)
    if data:
        decoded = bencodepy.decode(data)        
        return _extract_peers(decoded[b'peers'])


def _request_data_from_tracker(torrent_file: TorrentFile) -> bytes:
    params = {
            'info_hash': torrent_file.info_hash,
            'peer_id': gen_peer_id(),
            'port': PORT,
            'left': torrent_file.length,
            'uploaded': 0,
            'downloaded': 0,
            'compact': 1,
        }
    url = torrent_file.announce + '?' + urlencode(params)
    fp = urllib.request.urlopen(url)
    return fp.read()


def _extract_peers(data: bytes) -> List[Peer]:
    peers = []
    index = 0
    while index < len(data):
        ip = data[index:index+4]
        port = data[index+4:index+6]
        peers.append(
            Peer(
                ip=socket.inet_ntoa(ip),
                port=struct.unpack('>H', port)[0],
            ),
        )
        index += 6
    return peers
