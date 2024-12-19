import boa
import boa_solidity
import pytest

import os
import sys

sys.path.insert(0, os.getcwd())
from scripts.scrvusd import proof as proof_utils


def test_verifier(
    scrvusd_rate_verifier, scrvusd_rate_oracle, blockhash_oracle_mock, w3_eth, block_number
):
    # first fetch actual price
    real_price = proof_utils.scrvusd_pps(w3_eth, block_number)
    print(real_price)
    # prepare ground truth - mock blockhash oracle on the sidechain
    block_hash = w3_eth.eth.get_block(block_number).hash
    blockhash_oracle_mock.set_block_hash(block_number, block_hash)

    # prepare proof
    block_header_rlp, proof_rlp = proof_utils.generate_proof(
        w3_eth, block_number=block_number, log=False
    )

    previous_rate = scrvusd_rate_oracle.raw_price()
    print(previous_rate)
    assert previous_rate == 1000000000000000000  # we init at 1, might change later
    print(scrvusd_rate_verifier.verify(bytes.fromhex(block_header_rlp), bytes.fromhex(proof_rlp)))
    updated_rate = scrvusd_rate_oracle.raw_price(0, w3_eth.eth.get_block(block_number).timestamp)
    print(updated_rate)
    assert updated_rate > previous_rate  # must be higher
    assert updated_rate == 1019823606670401906  # new price at fixture block


# @pytest.mark.parametrize("w3_sidechain", ["taiko", "optimism"], indirect=True)
# def test_l2(w3_sidechain):
#     print(w3_sidechain.eth.chain_id)
#     assert True
