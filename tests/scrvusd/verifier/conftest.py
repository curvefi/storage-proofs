import pytest
import boa


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
