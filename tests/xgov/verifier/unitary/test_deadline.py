import boa
import pytest

import rlp

from scripts.xgov.proof import serialize_proofs
from tests.shared.verifier import get_block_and_proofs
from tests.xgov.conftest import CHAIN_ID
from tests.xgov.verifier.conftest import MESSAGES


@pytest.mark.parametrize("i", [0, 1, 2])
def test_verify_by_blockhash(verifier, broadcaster, relayer, boracle, verifier_slots, i):
    nonce = 0
    slots = verifier_slots(2**i, CHAIN_ID, nonce)
    block_header, proofs = get_block_and_proofs([(broadcaster, slots)])
    boracle._set_block_hash(block_header.block_number, block_header.hash)

    boa.env.time_travel(seconds=broadcaster.deadline(2**i, CHAIN_ID, nonce) - boa.env.timestamp + 1)
    relayer.renew_values()
    verifier.verifyMessagesByBlockHash(
        2**i,
        MESSAGES[i],
        rlp.encode(block_header),
        serialize_proofs(proofs[0]),
    )

    assert verifier.nonce(2**i) == nonce + 1
    assert relayer.agent() == 0
    assert relayer.messages() == []


@pytest.mark.parametrize("i", [0, 1, 2])
def test_verify_by_stateroot(verifier, broadcaster, relayer, boracle, verifier_slots, i):
    nonce = 0
    slots = verifier_slots(2**i, CHAIN_ID, nonce)
    block_header, proofs = get_block_and_proofs([(broadcaster, slots)])
    boracle._set_state_root(block_header.block_number, block_header.state_root)

    boa.env.time_travel(seconds=broadcaster.deadline(2**i, CHAIN_ID, nonce) - boa.env.timestamp + 1)
    relayer.renew_values()
    verifier.verifyMessagesByStateRoot(
        2**i,
        MESSAGES[i],
        block_header.block_number,
        serialize_proofs(proofs[0]),
    )

    assert verifier.nonce(2**i) == nonce + 1
    assert relayer.agent() == 0
    assert relayer.messages() == []
