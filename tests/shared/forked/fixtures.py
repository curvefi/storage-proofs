import pytest

from tests.shared.forked.settings import Chain, CHAINS_DICT


@pytest.fixture(scope="session")
def forked_rpc():
    def inner(chain: Chain):
        return CHAINS_DICT[chain]["rpc"]

    return inner
