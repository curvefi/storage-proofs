import pytest
from web3 import Web3

from tests.forked.settings import Chain, CHAINS_DICT


@pytest.fixture(scope="session")
def rpc():
    def inner(chain: Chain):
        return CHAINS_DICT[chain]["rpc"]
    return inner


@pytest.fixture()
def w3_eth():
    rpc_url = CHAINS_DICT["mainnet"]["rpc"]
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    assert w3.is_connected(), f"Failed to connect to mainnet ({rpc_url})"
    return w3


# parametrize the fixture to allow for different chains
@pytest.fixture(params=CHAINS_DICT.keys())
def w3_sidechain(request):
    chain_name = request.param  # Parameter passed by the test
    if chain_name not in CHAINS_DICT:
        pytest.fail(
            f"Unknown chain: {chain_name}. Available chains: {', '.join(CHAINS_DICT.keys())}"
        )

    rpc_url = CHAINS_DICT[chain_name]["rpc"]
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    assert w3.is_connected(), f"Failed to connect to chain {chain_name} ({rpc_url})"
    return w3
