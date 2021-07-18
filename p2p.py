import collections
import logging
import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Deque, Optional

from client import (
    Client,
    check_bitfield_index,
    load_client,
    send_interested,
    send_request,
    send_unchoke,
)
from messages import Message, handle_message, read_message
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
        self._piece_length = piece_length
        self._blocks = self._get_blocks(index, piece_length)
        self._block_data = collections.OrderedDict()
        self._status = PieceStatus.READY
        self._size = 0

    def enque(self, block: Block) -> None:
        self._blocks.appendleft(block)

    def deque(self) -> Block:
        return self._blocks.pop()

    def add_block_data(self, block: Block) -> None:
        logging.info(f'block: {block.begin} of piece: {block.index} has successfully downloaded')
        self._block_data[block.begin] = block.data
        self._size += len(block.data)

    def get_piece_result(self) -> bytearray:
        result = bytearray()
        for data in self._block_data.values():
            result.append(data)
        return result

    @property
    def status(self) -> PieceStatus:
        return self._status

    @status.setter
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

    def has_piece_downloaded(self):
        return self._size == self._piece_length

    def n_blocks(self):
        return len(self._blocks)


class PieceManager:
    def __init__(self, torrentfile: TorrentFile):
        self._pieces = self._get_pieces(torrentfile)
        self._piece_data = collections.OrderedDict()

    def enque(self, piece: Piece) -> None:
        self._pieces.appendleft(piece)

    def deque(self) -> Piece:
        return self._pieces.pop()

    def add_piece_data(self, piece: Piece):
        self._piece_data[piece._index] = piece.get_piece_result()

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

    def n_pieces(self):
        return len(self._pieces)


def download(torrentfile: TorrentFile):
    logging.info(f'start download file: {torrentfile.name}')
    piece_manager = PieceManager(torrentfile)
    peers = get_peers(torrentfile)
    for peer in peers:
        start_worker(peer, piece_manager, torrentfile)


def start_worker(peer: Peer, piece_manager: PieceManager, torrentfile: TorrentFile):
    client = load_client(peer, torrentfile.info_hash, gen_peer_id())
    if not client:
        return None
    send_interested(client.conn)
    send_unchoke(client.conn)
    for _ in range(piece_manager.n_pieces()):
        piece = piece_manager.deque()
        if not check_bitfield_index(client.bitfield, piece.index):
            piece_manager.enque(piece)
            continue
        download_piece(client, piece)
        if client.chocked or piece.status != PieceStatus.FINISHED:
            piece_manager.enque(piece)
            return None
        piece_manager.add_piece_data(piece)


def download_piece(client: Client, piece: Piece) -> None:
    logging.info(f'start download piece: {piece.index} from client: {client.conn.getsockname()[0]}')
    n_attempts = 5
    while True:
        for _ in range(piece.n_blocks()):
            if client.chocked:
                piece.status = PieceStatus.READY
                return None
            else:
                piece.status = PieceStatus.PENDING
            block = piece.deque()
            try:
                send_request(client.conn, block.index, block.begin, block.length)
            except OSError:
                return None
            message = read_message(client.conn)
            if not message:
                logging.info(f'There are no data for block: {block.begin}')
                return None
            elif message == 'keep_alive':
                logging.info(f'Keep alive message for block: {block.begin}')
                piece.enque(block)
                continue
            handle_message(message, client, block)
            if block.data:
                logging.info('add block data')
                piece.add_block_data(block)
            else:
                piece.enque(block)
        if piece.has_piece_downloaded():
            piece.status = PieceStatus.FINISHED
            logging.info(f'piece: {piece.index} has successfully downloaded')
            return None
        if n_attempts <= 0:
            return None
