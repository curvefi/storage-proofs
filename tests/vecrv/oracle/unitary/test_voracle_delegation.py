import boa

from tests.conftest import EMPTY_ADDRESS


def test_update_delegation(voracle, delegation_verifier, anne, leo):
    assert voracle.delegated(anne) == anne
    assert voracle.delegator(leo) == leo
    assert voracle.delegated(EMPTY_ADDRESS) == EMPTY_ADDRESS
    assert voracle.delegator(EMPTY_ADDRESS) == EMPTY_ADDRESS

    block_number = 333
    with boa.env.prank(delegation_verifier):
        voracle.update_delegation(anne, leo, block_number)

    assert voracle.delegated(anne) == leo
    assert voracle.delegator(leo) == anne
    assert voracle.last_block_number() == block_number

    with boa.env.prank(delegation_verifier):
        with boa.reverts():  # outdated update
            voracle.update_delegation(anne, EMPTY_ADDRESS, block_number - 1)
        voracle.update_delegation(anne, EMPTY_ADDRESS, block_number)  # rewrite

    assert voracle.delegated(anne) == anne
    assert voracle.delegator(leo) == leo
    assert voracle.delegated(EMPTY_ADDRESS) == EMPTY_ADDRESS
    assert voracle.delegator(EMPTY_ADDRESS) == EMPTY_ADDRESS
    assert voracle.last_block_number() == block_number
