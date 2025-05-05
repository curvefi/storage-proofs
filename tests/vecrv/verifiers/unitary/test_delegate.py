import pytest
import rlp
import boa

from scripts.scrvusd.proof import serialize_proofs
from tests.shared.verifier import get_block_and_proofs


@pytest.fixture(scope="module", autouse=True)
def set_delegate(delegate, admin, anne, leo):
    with boa.env.prank(admin):
        delegate.delegate_from(boa.env.evm.chain.chain_id, anne, leo)


def test_by_blockhash(delegation_verifier, delegate, delegate_slots, boracle, voracle, anne, leo):
    block_header, proofs = get_block_and_proofs([(delegate, delegate_slots(anne))])
    boracle._set_block_hash(block_header.block_number, block_header.hash)

    block_header_rlp = rlp.encode(block_header)
    proofs_rlp = serialize_proofs(proofs[0])
    delegation_verifier.verifyDelegationByBlockHash(anne, block_header_rlp, proofs_rlp)

    assert voracle.eval(f"self.delegation_from[{anne}]") == leo
    assert voracle.eval(f"self.delegation_to[{leo}]") == anne


def test_by_stateroot(delegation_verifier, delegate, delegate_slots, boracle, voracle, anne, leo):
    block_header, proofs = get_block_and_proofs([(delegate, delegate_slots(anne))])
    boracle._set_state_root(block_header.block_number, block_header.state_root)

    delegation_verifier.verifyDelegationByStateRoot(
        anne,
        block_header.block_number,
        serialize_proofs(proofs[0]),
    )

    assert voracle.eval(f"self.delegation_from[{anne}]") == leo
    assert voracle.eval(f"self.delegation_to[{leo}]") == anne
