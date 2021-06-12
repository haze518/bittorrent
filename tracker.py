import urllib.request
from urllib.parse import urlencode

from torrentfile import TorrentFile
from utils import gen_peer_id

PORT = 6881


def get_peers(torrent_file: TorrentFile):
    data = _request_data_from_tracker(torrent_file)
    return data


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

if __name__ == '__main__':
    from torrentfile import parse_torrent_file
    import os
    path = os.getcwd() + '/tests/data/debian-10.9.0-amd64-netinst.iso.torrent'
    torrent_file = parse_torrent_file(path)
    get_peers(torrent_file)