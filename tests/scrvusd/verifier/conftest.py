import pytest
import boa
import boa_solidity


MAX_BPS_EXTENDED = 1_000_000_000_000


@pytest.fixture(scope="module")
def verifier(admin, boracle, soracle):
    with boa.env.prank(admin):
        deployer = boa_solidity.load_partial_solc(
            "contracts/scrvusd/verifiers/ScrvusdVerifierV2.sol",
            compiler_args={
                "optimize": True,
                "optimize_runs": 200,
                "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=./node_modules/solidity-rlp",
            },
        )
        return deployer.deploy(boracle.address, soracle.address)
