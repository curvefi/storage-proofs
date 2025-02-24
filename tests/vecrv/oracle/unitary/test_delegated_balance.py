import boa

from tests.conftest import WEEK, EMPTY_ADDRESS


def test_update_balance(voracle, delegation_verifier, vecrv_verifier, anne, leo):
    boa.env.time_travel(seconds=WEEK - boa.env.timestamp % WEEK)
    epoch = 100
    point = [
        10**18,  # bias
        1,  # slope
        boa.env.timestamp,  # ts
        0,  # blk – unused
    ]
    locked = [
        10**18,
        WEEK * 256,
    ]
    block_number = 333
    with boa.env.prank(vecrv_verifier):
        voracle.update_balance(
            anne,
            epoch,
            point,
            locked,
            block_number,
        )
    with boa.env.prank(delegation_verifier):
        voracle.update_delegation(anne, leo, block_number)

    for i in range(5):
        assert voracle.balanceOf(anne) == 0
        assert voracle.balanceOf(leo) == point[0] - point[1] * WEEK * i
        boa.env.time_travel(seconds=WEEK)
    assert voracle.get_last_user_slope(anne) == 0
    assert voracle.get_last_user_slope(leo) == point[1]
    assert voracle.locked__end(anne) == 0
    assert voracle.locked__end(leo) == locked[1]

    with boa.env.prank(delegation_verifier):  # revoke delegation
        voracle.update_delegation(anne, EMPTY_ADDRESS, block_number)

    for i in range(5, 10):
        assert voracle.balanceOf(anne) == point[0] - point[1] * WEEK * i
        assert voracle.balanceOf(leo) == 0
        boa.env.time_travel(seconds=WEEK)
    assert voracle.get_last_user_slope(anne) == point[1]
    assert voracle.get_last_user_slope(leo) == 0
    assert voracle.locked__end(anne) == locked[1]
    assert voracle.locked__end(leo) == 0
