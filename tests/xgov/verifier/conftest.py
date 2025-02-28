import boa
import boa_solidity
import pytest

from scripts.xgov.proof import hashmap


@pytest.fixture(scope="module")
def verifier(admin, boracle, relayer):
    with boa.env.prank(admin):
        deployer = boa_solidity.load_partial_solc(
            "tests/xgov/contracts/curve-xdao/contracts/verifiers/MessageDigestVerifier.sol",
            compiler_args={
                "optimize": True,
                "optimize_runs": 200,
                "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=./node_modules/solidity-rlp",
            },
        )
        return deployer.deploy(boracle.address, relayer.address)


@pytest.fixture(scope="module", autouse=True)
def set_verifier(relayer, verifier):
    with boa.env.prank(relayer.OWNERSHIP_AGENT()):
        relayer.set_messenger(verifier)


@pytest.fixture(scope="module")
def verifier_slots():
    def inner(agent, chain_id, nonce):
        message_digest_slot = hashmap(
            hashmap(hashmap(8, agent, "uint256"), chain_id, "uint256"),
            nonce,
            "uint256",
        )
        deadline_slot = hashmap(
            hashmap(hashmap(9, agent, "uint256"), chain_id, "uint256"),
            nonce,
            "uint256",
        )
        return [message_digest_slot, deadline_slot]

    return inner
