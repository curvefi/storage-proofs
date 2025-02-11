import pytest

import boa

from tests.conftest import EMPTY_BYTES32
from tests.shared.forked.fixtures import Chain


@pytest.fixture(scope="module", autouse=True)
def set_network(forked_rpc):
    # return to previous env after
    boa.fork(forked_rpc(Chain.SONIC))
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"


@pytest.fixture(scope="module")
def boracle(set_network):
    return boa.load(
        "contracts/blockhash/SonicBlockHashOracle.vy", "0x836664B0c0CB29B7877bCcF94159CC996528F2C3"
    )


@pytest.mark.parametrize("operation", ["commit", "apply"])
def test_update(boracle, anne, operation):
    with boa.env.prank(anne):
        number = getattr(boracle, operation)()

    stateroot = boracle.get_state_root(number)
    assert stateroot != EMPTY_BYTES32, "StateRoot not set"
    assert (
        boracle.commitments(anne, number) == stateroot if operation == "commit" else EMPTY_BYTES32
    ), "Commitment not registered"
    assert boracle.find_known_block_number() == number, "Could not find new block"
    assert boracle.find_known_block_number(number) == number, "Could not find new block"
    assert boracle.find_known_block_number(number + 10) == number, "Could not find new block"
    assert boracle.find_known_block_number(number + 100) == number, "Could not find new block"

    with boa.reverts():  # Not supported
        boracle.get_block_hash(number)
    # with boa.reverts():  # No previously known blocks
    #     boracle.find_known_block_number(number - 1)


def test_current_block(boracle):
    state_oracle = boa.loads_abi(
        '[{"inputs":[],"name":"lastBlockNum","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lastState","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"}]',
    ).at("0x836664B0c0CB29B7877bCcF94159CC996528F2C3")

    block_number = state_oracle.lastBlockNum()
    stateroot = state_oracle.lastState()
    assert boracle.get_state_root(block_number) == stateroot, "Could not fetch current data"

    with boa.reverts():  # Not supported
        boracle.get_state_root(block_number + 1)
