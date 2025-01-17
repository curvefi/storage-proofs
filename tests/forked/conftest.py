import pytest
from web3 import Web3

from tests.forked.settings import Chain, CHAINS_DICT


@pytest.fixture(scope="session")
def rpc():
    def inner(chain: Chain):
        return CHAINS_DICT[chain]["rpc"]
    return inner
