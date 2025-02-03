import pytest
import rlp
import boa

from scripts.scrvusd.proof import serialize_proofs
from tests.conftest import WEEK
from tests.scrvusd.verifier.conftest import MAX_BPS_EXTENDED
from tests.shared.verifier import get_block_and_proofs


@pytest.fixture(scope="module")
def scrvusd_slot_values(scrvusd, crvusd, admin, anne):
    deposit = 10 ** 18
    with boa.env.prank(anne):
        crvusd._mint_for_testing(anne, deposit)
        crvusd.approve(scrvusd, deposit)
        scrvusd.deposit(deposit, anne)
        # total_idle = deposit
        # total_supply = deposit

    rewards = 10 ** 17
    with boa.env.prank(admin):
        crvusd._mint_for_testing(scrvusd, rewards)
        scrvusd.process_report(scrvusd)

    boa.env.time_travel(seconds=12, block_delta=12)
    return [
        0,  # total_debt, actually doesn't exist
        deposit + rewards,  # total_idle
        deposit + rewards,  # total_supply
        boa.env.evm.patch.timestamp - 12 + WEEK,  # full_profit_unlock_date
        rewards * MAX_BPS_EXTENDED // WEEK,  # profit_unlocking_rate
        boa.env.evm.patch.timestamp - 12,  # last_profit_update
        rewards,  # balance_of_self
    ]


def test_by_blockhash(verifier, soracle_slots, soracle, boracle, scrvusd, scrvusd_slot_values):
    block_header, proofs = get_block_and_proofs([(scrvusd, soracle_slots)])
    boracle._set_block_hash(block_header.block_number, block_header.hash)
    block_header_rlp = rlp.encode(block_header)
    proofs_rlp = serialize_proofs(proofs[0])
    verifier.verifyScrvusdByBlockHash(block_header_rlp, proofs_rlp)

    assert soracle._storage.parameters.get() == scrvusd_slot_values
    assert soracle.ts() == block_header.timestamp
    assert soracle.block_number() == block_header.block_number


def test_by_stateroot(verifier, soracle_slots, soracle, boracle, scrvusd, scrvusd_slot_values):
    block_header, proofs = get_block_and_proofs([(scrvusd, soracle_slots)])
    boracle._set_state_root(block_header.block_number, block_header.state_root)
    verifier.verifyScrvusdByStateRoot(
        block_header.block_number,
        serialize_proofs(proofs[0]),
    )

    assert soracle._storage.parameters.get() == scrvusd_slot_values
    assert soracle.ts() == scrvusd_slot_values[5]
    assert soracle.block_number() == block_header.block_number
