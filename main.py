import p2p
import sys
import torrentfile

import logging
import os

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main(path: str):
    torrent_file = torrentfile.parse_torrent_file(path)
    p2p.download(torrent_file)


if __name__ == '__main__':
    path = os.getcwd() + '/tests/data/debian-10.9.0-amd64-netinst.iso.torrent'
    main(path)
