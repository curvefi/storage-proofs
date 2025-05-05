import pytest

from web3 import Web3

from tests.shared.forked.settings import Chain, CHAINS_DICT


@pytest.fixture(scope="session")
def forked_rpc():
    def inner(chain: Chain):
        return CHAINS_DICT[chain]["rpc"]

    return inner


@pytest.fixture(scope="module")
def eth_web3(forked_rpc):
    return Web3(provider=Web3.HTTPProvider(forked_rpc(Chain.ETH)))
