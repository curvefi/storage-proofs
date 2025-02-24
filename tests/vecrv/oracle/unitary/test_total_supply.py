import boa

from tests.conftest import WEEK


def test_update_total(voracle, vecrv_verifier):
    boa.env.time_travel(seconds=WEEK - boa.env.timestamp % WEEK)
    epoch = 100
    point = [
        10**18,  # bias
        1,  # slope
        boa.env.timestamp,  # ts
        0,  # blk – unused
    ]
    slope_changes = [-2, 2, -2, 2]
    block_number = 333
    with boa.env.prank(vecrv_verifier):
        voracle.update_total(
            epoch,
            point,
            slope_changes,
            block_number,
        )

    assert voracle.totalSupply() == point[0]
    for i in range(5):
        boa.env.time_travel(seconds=WEEK)
        assert voracle.totalSupply() == point[0] - (0 if i % 2 else WEEK)

    with boa.env.prank(vecrv_verifier):
        with boa.reverts():  # outdated update
            voracle.update_total(
                epoch,
                point,
                slope_changes,
                block_number - 1,
            )
        voracle.update_total(  # rewrite
            epoch + 1,
            point,
            slope_changes,
            block_number,
        )
