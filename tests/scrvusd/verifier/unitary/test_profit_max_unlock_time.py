import pytest
import rlp
import boa

from scripts.scrvusd.proof import serialize_proofs
from tests.shared.verifier import get_block_and_proofs


@pytest.fixture(scope="module")
def scrvusd_period(scrvusd, admin):
    new_period = 8 * 86400
    with boa.env.prank(admin):
        scrvusd.setProfitMaxUnlockTime(new_period)
    return new_period


def test_by_blockhash(verifier, soracle_period_slots, soracle, boracle, scrvusd, scrvusd_period):
    block_header, proofs = get_block_and_proofs([(scrvusd, soracle_period_slots)])
    boracle._set_block_hash(block_header.block_number, block_header.hash)

    block_header_rlp = rlp.encode(block_header)
    proofs_rlp = serialize_proofs(proofs[0])
    verifier.verifyPeriodByBlockHash(block_header_rlp, proofs_rlp)

    assert soracle.profit_max_unlock_time() == scrvusd_period
    assert soracle.block_number() == block_header.block_number


def test_by_stateroot(verifier, soracle_period_slots, soracle, boracle, scrvusd, scrvusd_period):
    block_header, proofs = get_block_and_proofs([(scrvusd, soracle_period_slots)])
    boracle._set_state_root(block_header.block_number, block_header.state_root)

    verifier.verifyPeriodByStateRoot(
        block_header.block_number,
        serialize_proofs(proofs[0]),
    )

    assert soracle.profit_max_unlock_time() == scrvusd_period
    assert soracle.block_number() == block_header.block_number
