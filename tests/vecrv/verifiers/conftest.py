import pytest
import boa
import boa_solidity


@pytest.fixture(scope="module")
def delegation_verifier(admin, boracle, voracle):
    with boa.env.prank(admin):
        deployer = boa_solidity.load_partial_solc(
            "contracts/vecrv/verifiers/DelegationVerifier.sol",
            compiler_args={
                "optimize": True,
                "optimize_runs": 200,
                "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=./node_modules/solidity-rlp",
            },
        )
        return deployer.deploy(boracle.address, voracle.address)


@pytest.fixture(scope="module")
def vecrv_verifier(admin, boracle, voracle):
    with boa.env.prank(admin):
        deployer = boa_solidity.load_partial_solc(
            "contracts/vecrv/verifiers/VecrvVerifier.sol",
            compiler_args={
                "optimize": True,
                "optimize_runs": 200,
                "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=./node_modules/solidity-rlp",
            },
        )
        return deployer.deploy(boracle.address, voracle.address)
