import pytest

import boa

from scripts.vecrv.proof import generate_balance_proof, generate_total_proof
from tests.conftest import WEEK
from tests.shared.forked.fixtures import Chain


CONVEX = "0x989AEb4d175e16225E39E87d0D97A3360524AD80"


@pytest.fixture(scope="module", autouse=True)
def set_network(forked_rpc):
    # return to previous env after
    boa.fork(forked_rpc(Chain.ETH))
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"


@pytest.fixture(scope="module")
def vecrv(eth_web3):
    return boa.load_abi("tests/vecrv/contracts/abi/Vecrv.json", name="vecrv").at(
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2"
    )


@pytest.fixture(scope="module")
def block(eth_web3):
    return eth_web3.eth.get_block("finalized")


def test_verify_convex_by_blockhash(vecrv_verifier, boracle, voracle, eth_web3, vecrv, block):
    block_header, proofs = generate_balance_proof(CONVEX, eth_web3, block_number=block.number)
    boracle._set_block_hash(block.number, block.hash)

    vecrv_verifier.verifyBalanceByBlockHash(
        CONVEX,
        bytes.fromhex(block_header),
        bytes.fromhex(proofs),
    )

    # balance
    assert (user_point_epoch := voracle.user_point_epoch(CONVEX)) == vecrv.user_point_epoch(CONVEX)
    assert voracle.user_point_history(CONVEX, user_point_epoch) == vecrv.user_point_history(
        CONVEX, user_point_epoch
    )
    assert voracle.locked(CONVEX) == vecrv.locked(CONVEX)

    # total supply
    assert (epoch := voracle.epoch()) == vecrv.epoch()
    assert (point_history := voracle.point_history(epoch)) == vecrv.point_history(epoch)
    start_time = WEEK + (point_history.ts // WEEK) * WEEK
    for i in range(4):
        assert voracle.slope_changes(start_time + WEEK * i) == vecrv.slope_changes(
            start_time + WEEK * i
        )

    assert voracle.last_block_number() == block.number


def test_verify_total_by_blockhash(vecrv_verifier, boracle, voracle, eth_web3, vecrv, block):
    block_header, proofs = generate_total_proof(eth_web3, block_number=block.number)
    boracle._set_block_hash(block.number, block.hash)

    vecrv_verifier.verifyTotalByBlockHash(
        bytes.fromhex(block_header),
        bytes.fromhex(proofs),
    )

    assert (epoch := voracle.epoch()) == vecrv.epoch()
    assert (point_history := voracle.point_history(epoch)) == vecrv.point_history(epoch)
    start_time = WEEK + (point_history.ts // WEEK) * WEEK
    for i in range(4):
        assert voracle.slope_changes(start_time + WEEK * i) == vecrv.slope_changes(
            start_time + WEEK * i
        )

    assert voracle.last_block_number() == block.number
