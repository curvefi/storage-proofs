import boa

from tests.conftest import WEEK


def test_update_balance(voracle, vecrv_verifier, anne):
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

    for i in range(5):
        assert voracle.balanceOf(anne) == point[0] - point[1] * WEEK * i
        boa.env.time_travel(seconds=WEEK)
    assert voracle.get_last_user_slope(anne) == point[1]
    assert voracle.locked__end(anne) == locked[1]

    with boa.env.prank(vecrv_verifier):
        with boa.reverts():  # outdated update
            voracle.update_balance(
                anne,
                epoch,
                point,
                locked,
                block_number - 1,
            )
        voracle.update_balance(  # rewrite
            anne,
            epoch + 1,
            point,
            locked,
            block_number,
        )
