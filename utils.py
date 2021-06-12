import random
from functools import lru_cache


@lru_cache
def gen_peer_id():
    """По протоколу длина id должна быть равна 20."""
    return ('-PC0001-' + ''.join(
        [str(random.randint(0, 9)) for _ in range(12)]
    )).encode('utf-8')
