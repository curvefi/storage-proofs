import pytest
import rlp
import boa

from scripts.scrvusd.proof import serialize_proofs
from tests.conftest import WEEK
from tests.scrvusd.verifier.conftest import MAX_BPS_EXTENDED
from tests.shared.verifier import get_block_and_proofs


@pytest.fixture(scope="module")
def scrvusd_slot_values(scrvusd, crvusd, admin, anne):
    deposit = 10**18
    with boa.env.prank(anne):
        crvusd._mint_for_testing(anne, deposit)
        crvusd.approve(scrvusd, deposit)
        scrvusd.deposit(deposit, anne)
        # New scrvusd parameters:
        #   scrvusd.total_idle = deposit,
        #   scrvusd.total_supply = deposit.

    rewards = 10**17
    with boa.env.prank(admin):
        crvusd._mint_for_testing(scrvusd, rewards)
        scrvusd.process_report(scrvusd)
        # Minted `rewards` shares to scrvusd, because price is still == 1.

    boa.env.time_travel(seconds=12, block_delta=12)
    return {
        "total_debt": 0,  # actually doesn't exist
        "total_idle": deposit + rewards,
        "total_supply": deposit + rewards,
        "full_profit_unlock_date": boa.env.evm.patch.timestamp - 12 + WEEK,
        "profit_unlocking_rate": rewards * MAX_BPS_EXTENDED // WEEK,
        "last_profit_update": boa.env.evm.patch.timestamp - 12,
        "balance_of_self": rewards,
    }


def test_by_blockhash(
    verifier, soracle_price_slots, soracle, boracle, scrvusd, scrvusd_slot_values
):
    block_header, proofs = get_block_and_proofs([(scrvusd, soracle_price_slots)])
    boracle._set_block_hash(block_header.block_number, block_header.hash)

    verifier.verifyScrvusdByBlockHash(
        rlp.encode(block_header),
        serialize_proofs(proofs[0]),
    )

    assert soracle._storage.price_params.get() == scrvusd_slot_values
    assert soracle._storage.price_params_ts.get() == block_header.timestamp
    assert soracle.last_block_number() == block_header.block_number


def test_by_stateroot(
    verifier, soracle_price_slots, soracle, boracle, scrvusd, scrvusd_slot_values
):
    block_header, proofs = get_block_and_proofs([(scrvusd, soracle_price_slots)])
    boracle._set_state_root(block_header.block_number, block_header.state_root)

    verifier.verifyScrvusdByStateRoot(
        block_header.block_number,
        serialize_proofs(proofs[0]),
    )

    assert soracle._storage.price_params.get() == scrvusd_slot_values
    assert soracle._storage.price_params_ts.get() == scrvusd_slot_values["last_profit_update"]
    assert soracle.last_block_number() == block_header.block_number
