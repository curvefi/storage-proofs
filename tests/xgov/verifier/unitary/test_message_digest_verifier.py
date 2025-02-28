import pytest

import rlp

from scripts.xgov.proof import serialize_proofs
from tests.shared.verifier import get_block_and_proofs
from tests.xgov.conftest import CHAIN_ID
from tests.xgov.verifier.conftest import NONCES, MESSAGES


@pytest.mark.parametrize("i", [0, 1, 2])
def test_verify_by_blockhash(verifier, broadcaster, relayer, boracle, verifier_slots, i):
    slots = []
    for nonce in range(NONCES[i] + 1):
        slots.append(verifier_slots(2**i, CHAIN_ID, nonce))
    block_header, proofs = get_block_and_proofs([(broadcaster, s) for s in slots])
    boracle._set_block_hash(block_header.block_number, block_header.hash)

    for nonce in range(NONCES[i] + 1):
        relayer.renew_values()
        verifier.verifyMessagesByBlockHash(
            2**i,
            MESSAGES[i],
            rlp.encode(block_header),
            serialize_proofs(proofs[nonce]),
        )

        assert verifier.nonce(2**i) == nonce + 1
        assert relayer.agent() == 2**i
        assert relayer.messages() == MESSAGES[i]


@pytest.mark.parametrize("i", [0, 1, 2])
def test_verify_by_stateroot(verifier, broadcaster, relayer, boracle, verifier_slots, i):
    slots = []
    for nonce in range(NONCES[i] + 1):
        slots.append(verifier_slots(2**i, CHAIN_ID, nonce))
    block_header, proofs = get_block_and_proofs([(broadcaster, s) for s in slots])
    boracle._set_state_root(block_header.block_number, block_header.state_root)

    for nonce in range(NONCES[i] + 1):
        relayer.renew_values()
        verifier.verifyMessagesByStateRoot(
            2**i,
            MESSAGES[i],
            block_header.block_number,
            serialize_proofs(proofs[nonce]),
        )

        assert verifier.nonce(2**i) == nonce + 1
        assert relayer.agent() == 2**i
        assert relayer.messages() == MESSAGES[i]
