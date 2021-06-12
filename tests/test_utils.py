from utils import gen_peer_id


def test_gen_peer_id():
    peer_id = gen_peer_id()
    assert len(peer_id) == 20
    assert peer_id == gen_peer_id()
