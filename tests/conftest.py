import pytest

import phoenix
from phoenix import params

REAL_SETS = [params.PHOENIX509, params.PHOENIX677, params.PHOENIX821]
ALL_SETS = [params.TOY, *REAL_SETS]


@pytest.fixture(scope="session", params=ALL_SETS, ids=lambda ps: ps.name)
def keypair(request):
    return phoenix.generate_keypair(request.param, seed=b"test-" + request.param.name.encode())


@pytest.fixture(scope="session")
def default_keypair():
    return phoenix.generate_keypair(seed=b"default")
