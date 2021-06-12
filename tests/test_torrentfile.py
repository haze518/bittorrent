import pytest
from torrentfile import parse_torrent_file


def test_torrentfile(torrent_file_path):
    data = parse_torrent_file(torrent_file_path)
    assert data.announce == 'http://bttracker.debian.org:6969/announce'
    assert data.name == 'debian-10.9.0-amd64-netinst.iso'
    assert data.length == 353370112
    assert data.piece_length == 262144
    assert len(data.piece_hashes) == round(data.length/data.piece_length)
