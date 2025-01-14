import pytest

import boa

from conftest import EMPTY_BYTES32
from tests.forked.conftest import Chain


@pytest.fixture(scope="module", autouse=True)
def set_network(rpc):
    # return to previous env after
    boa.fork(rpc(Chain.MANTLE))
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"


@pytest.fixture(scope="module")
def boracle(set_network):
    return boa.load("contracts/blockhash/OptimismBlockHashOracle.vy")


@pytest.mark.parametrize("operation", ["commit", "apply"])
def test_update(boracle, alice, operation):
    with boa.env.prank(alice):
        number = getattr(boracle, operation)()

    blockhash = boracle.get_block_hash(number)
    assert blockhash != EMPTY_BYTES32, "BlockHash not set"
    assert boracle.commitments(alice, number) == blockhash if operation == "commit" else EMPTY_BYTES32, \
        "Commitment not registered"
    assert boracle.find_known_block_number() == number, "Could not find new block"
    assert boracle.find_known_block_number(number) == number, "Could not find new block"
    assert boracle.find_known_block_number(number + 10) == number, "Could not find new block"
    assert boracle.find_known_block_number(number + 100) == number, "Could not find new block"

    with boa.reverts():  # Not supported
        boracle.get_state_root(number)
    # with boa.reverts():  # No previously known blocks
    #     boracle.find_known_block_number(number - 1)


def test_current_block(boracle):
    l1_block = boa.loads_abi(
        '[{"inputs":[],"name":"number","outputs":[{"internalType":"uint64","name":"","type":"uint64"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"hash","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"}]',
    ).at("0x4200000000000000000000000000000000000015")

    block_number = l1_block.number()
    blockhash = l1_block.hash()
    assert boracle.get_block_hash(block_number) == blockhash, "Could not fetch current data"

    with boa.reverts():  # Not supported
        boracle.get_block_hash(block_number + 1)
