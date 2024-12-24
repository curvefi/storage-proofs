import pytest

import boa

H_STATE_ROOT = bytes.fromhex("73e6d340850343cc6f001515dc593377337c95a6ffe034fe1e844d4dab5da169")


@pytest.fixture(scope="module", autouse=True)
def set_network():
    # return to previous env after
    boa.fork(f"https://rpc.taiko.xyz", block_identifier=707157)
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"


@pytest.fixture(scope="module")
def boracle(set_network):
    return boa.load("contracts/blockhash/TaikoBlockHashOracle.vy")


def test_header(boracle):
    assert boracle.H_STATE_ROOT() == H_STATE_ROOT


def test_current_block(boracle):
    state_oracle = boa.loads_abi(
        '[{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"},{"internalType":"bytes32","name":"_kind","type":"bytes32"},{"internalType":"uint64","name":"_blockId","type":"uint64"}],"name":"getSyncedChainData","outputs":[{"internalType":"uint64","name":"blockId_","type":"uint64"},{"internalType":"bytes32","name":"chainData_","type":"bytes32"}],"stateMutability":"view","type":"function"}]',
    ).at("0x1670000000000000000000000000000000000005")

    block_number = boracle.find_known_block_number(21473506)
    block_number, stateroot = state_oracle.getSyncedChainData(1, H_STATE_ROOT, block_number)
    assert boracle.get_state_root(block_number) == stateroot, "Could not fetch current data"

    with boa.reverts():  # Not supported
        boracle.get_state_root(block_number + 1)
