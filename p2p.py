import collections
import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Deque

from client import (
    Client,
    check_bitfield_index,
    load_client,
    send_interested,
    send_request,
    send_unchoke,
)
from messages import handle_message, read_message
from torrentfile import TorrentFile
from tracker import Peer, get_peers
from utils import gen_peer_id

BLOCK_SIZE = 2**14  # стандартный размер блока


@dataclass
class Block:
    length: int
    begin: int
    index: int
    data: bytes = b''


class PieceStatus(Enum):
    READY = auto()
    PENDING = auto()
    FINISHED = auto()


class Piece:
    def __init__(self, index: int, piece_hash: bytes, piece_length: int):
        self._index = index
        self._piece_hash = piece_hash  # нужен для дальнейшей проверки sha1 скачанного куска
        self._blocks = self._get_blocks(index, piece_length)
        self._block_data = collections.OrderedDict()
        self._status = PieceStatus.READY

    def enque(self, block: Block) -> None:
        self._blocks.appendleft(block)

    def deque(self) -> Block:
        return self._blocks.pop()

    def add_block_data(self, block: Block) -> None:
        self._block_data[block.begin] = block.data

    def get_piece_result(self):
        return sum([piece_data for piece_data in self._block_data.values()])

    @property
    def status(self) -> PieceStatus:
        return self._status
    
    @property.setter
    def status(self, status: PieceStatus) -> PieceStatus:
        self._status = status

    @property
    def index(self):
        return self._index

    def _get_blocks(self, index: int, piece_length: int) -> Deque[Block]:
        number_of_blocks = math.ceil(piece_length/BLOCK_SIZE)
        blocks = [Block(length=BLOCK_SIZE, begin=BLOCK_SIZE*n, index=index) for n in range(number_of_blocks)]
        if piece_length%BLOCK_SIZE != 0:  # последний блок может быть меньше, чем другие
            blocks[-1] = Block(length=piece_length%BLOCK_SIZE, begin=BLOCK_SIZE*number_of_blocks, index=index)
        return collections.deque(blocks)

    def __len__(self):
        return len(self._blocks)


class PieceManager:
    def __init__(self, torrentfile: TorrentFile):
        self._pieces = self._get_pieces(torrentfile)
        self._piece_data = collections.OrderedDict()

    def enque(self, piece: Piece) -> None:
        self.pieces.appendleft(piece)

    def deque(self) -> Piece:
        return self.pieces.pop()

    def add_piece_data(self, piece: Piece):
        self._piece_data[piece._index]

    def _get_pieces(self, torrentfile: TorrentFile) -> Deque[Piece]:
        pieces = collections.deque()
        for idx, piece_hash in enumerate(torrentfile.piece_hashes):
            piece_length = torrentfile.piece_length
            if idx == len(torrentfile.piece_hashes) - 1:
                piece_length = torrentfile.length % piece_length  # последняя часть меньше остальных
            pieces.append(
                Piece(idx, piece_hash, piece_length)
            )
        return pieces

    def __len__(self):
        return len(self._pieces)


def download(torrentfile: TorrentFile):
    piece_manager = PieceManager(torrentfile)
    peers = get_peers(torrentfile)
    for peer in peers:
        start_worker(peer, piece_manager, torrentfile)


def start_worker(peer: Peer, piece_manager: PieceManager, torrentfile: TorrentFile):
    client = load_client(peer, torrentfile.info_hash, gen_peer_id())
    send_interested(client.conn)
    send_unchoke(client.conn)
    for _ in range(len(piece_manager)):
        piece = piece_manager.deque()
        if not check_bitfield_index(client.bitfield, piece.index):
            piece_manager.enque(piece)
            continue
        download_piece(client, piece)
        if client.chocked or piece.status != PieceStatus.FINISHED:
            piece_manager.enque(piece)
            return None
        piece_manager.add_piece_data(piece)


def download_piece(client: Client, piece: Piece):
    while True:
        for _ in range(len(piece)):
            if client.chocked:
                piece.status = PieceStatus.READY
                return None
            else:
                piece.status = PieceStatus.PENDING
            block = piece.deque()
            send_request(client.conn, block.index, block.begin, block.length)
            message = read_message(client.conn)
            handle_message(message, client, block)
            if block.data:
               piece.add_block_data(block)
            else:
                piece.enque(block)
        if not len(piece):
            piece.status = PieceStatus.FINISHED
            return None
