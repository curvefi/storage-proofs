import boa
import pytest
import os
from web3 import Web3

CHAINS_DICT = {
    "mainnet": {"id": 1, "rpc": os.getenv("ETH_RPC_URL") or "https://eth.drpc.org"},
    "optimism": {
        "id": 10,
        "rpc": "https://mainnet.optimism.io",
    },
    "base": {"id": 8453, "rpc": "https://mainnet.base.org"},
    "fraxtal": {"id": 252, "rpc": "https://rpc.frax.com"},
    "mantle": {"id": 5000, "rpc": "https://rpc.mantle.xyz/"},
    "arbitrum": {
        "id": 42161,
        "rpc": "https://arb1.arbitrum.io/rpc",
    },
    "taiko": {"id": 167000, "rpc": "https://taiko.drpc.org"},
    "sonic": {"id": 146, "rpc": "https://rpc.soniclabs.com"},
}


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
