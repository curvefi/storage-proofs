import boa
import boa_solidity
import pytest

CURVE_DAO = boa.env.generate_address()
DEFAULT_BLOCK_NUMBER = 21369420
DEFAULT_BLOCK_HASH = bytes.fromhex(
    "37CFBA409B3C9763A464565798C166B007C29F613ED9900C2EFA6342A3A5A65C"
)


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
        contract = contract_deployer(10**18, 10**10)
        contract.set_verifier(verifier_mock)
    return contract


@pytest.fixture()
def scrvusd_rate_verifier(blockhash_oracle_mock, scrvusd_rate_oracle, dev_deployer):
    contract_deployer = boa.load_partial_solc(
        "contracts/scrvusd/verifiers/ScrvusdVerifier.sol",
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
