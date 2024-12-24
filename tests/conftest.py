import boa
import boa_solidity

import pytest
import os
from web3 import Web3

CURVE_DAO = boa.env.generate_address()
DEFAULT_BLOCK_NUMBER = 21369420
DEFAULT_BLOCK_HASH = bytes.fromhex(
    "37CFBA409B3C9763A464565798C166B007C29F613ED9900C2EFA6342A3A5A65C"
)

CHAINS_DICT = {
    "mainnet": {
        "id": 1,
        "rpc": f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['WEB3_ETHEREUM_MAINNET_ALCHEMY_PROJECT_ID']}",
    },
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


@pytest.fixture
def alice():
    return boa.env.generate_address()


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


@pytest.fixture()
def block_number():
    return DEFAULT_BLOCK_NUMBER


@pytest.fixture()
def curve_dao():
    return CURVE_DAO


@pytest.fixture()
def dev_deployer():
    return boa.env.generate_address()


@pytest.fixture()
def verifier_mock():
    return boa.env.generate_address()


@pytest.fixture()
def blockhash_oracle_mock(dev_deployer):
    contract_deployer = boa.load_partial("tests/mocks/BlockhashOracleMock.vy")
    with boa.env.prank(dev_deployer):
        contract = contract_deployer(DEFAULT_BLOCK_HASH)
    return contract


@pytest.fixture()
def scrvusd_rate_oracle(dev_deployer, verifier_mock):
    contract_deployer = boa.load_partial("contracts/scrvusd/oracles/ScrvusdOracleV2.vy")
    with boa.env.prank(dev_deployer):
        contract = contract_deployer(10**18)
        contract.set_verifier(verifier_mock)
    return contract


@pytest.fixture()
def scrvusd_rate_verifier(blockhash_oracle_mock, scrvusd_rate_oracle, dev_deployer):
    contract_deployer = boa.load_partial_solc(
        "contracts/scrvusd/verifiers/ScrvusdVerifierBasic.sol",
        compiler_args={
            "optimize": True,
            "optimize_runs": 200,
            "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=./node_modules/solidity-rlp",
        },
    )
    with boa.env.prank(dev_deployer):
        contract = contract_deployer.deploy(
            blockhash_oracle_mock.address, scrvusd_rate_oracle.address
        )
        scrvusd_rate_oracle.set_verifier(contract)
    return contract
