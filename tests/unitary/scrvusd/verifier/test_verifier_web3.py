import boa
import boa_solidity
import pytest

import os
import sys

sys.path.insert(0, os.getcwd())
from scripts.scrvusd.proof import *  # noqa: F403


def test_verifier(scrvusd_rate_verifier, blockhash_oracle_mock, w3_eth, block_number):
    # print(blockhash_oracle_mock.get_block_hash(0))
    print(w3_eth.eth.get_block(block_number))
    print(w3_eth.eth.chain_id)

    assert True


# @pytest.mark.parametrize("w3_sidechain", ["taiko", "optimism"], indirect=True)
# def test_l2(w3_sidechain):
#     print(w3_sidechain.eth.chain_id)

#     assert True
