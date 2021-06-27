from torrentfile import parse_torrent_file
from p2p import Piece


def test_piece(torrent_file_path):
    data = parse_torrent_file(torrent_file_path)
    piece = Piece(0, data.piece_hashes[0], data.piece_length)
    assert sum([block.length for block in piece.blocks]) == data.piece_length


def test_last_piece(torrent_file_path):
    data = parse_torrent_file(torrent_file_path)
    piece = Piece(0, data.piece_hashes[0], data.piece_length-1)  # последний кусок меньше остальных
    assert sum([block.length for block in piece.blocks]) == data.piece_length - 1
