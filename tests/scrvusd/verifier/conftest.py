import pytest
import boa
import boa_solidity


MAX_BPS_EXTENDED = 1_000_000_000_000


@pytest.fixture(scope="module")
def verifier(admin, scrvusd, boracle, soracle):
    with boa.env.prank(admin):
        deployer = boa_solidity.load_partial_solc(
            "contracts/scrvusd/verifiers/ScrvusdVerifierBasic.sol",
            compiler_args={
                "optimize": True,
                "optimize_runs": 200,
                "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=./node_modules/solidity-rlp",
            },
        )
        return deployer.deploy(scrvusd.address, boracle.address, soracle.address)
