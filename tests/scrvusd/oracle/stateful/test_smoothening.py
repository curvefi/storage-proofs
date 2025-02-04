import functools

import boa
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import invariant, run_state_machine_as_test, given

from tests.scrvusd.oracle.stateful.crvusd_state_machine import SoracleStateMachine
import pytest


PERIOD_CHECK_DURATION = 4 * 7 * 86400  # in seconds


class SmootheningStateMachine(SoracleStateMachine):
    """
    State machine for testing price smoothening.

    Decomposed smoothening since it impacts on price and makes hard to check actual values.
    It is still possible to reach value without smoothening via `.raw_price()`,
    though the purpose is to test final methods.
    """

    # Force-including 0 and 1 as basic values to check
    st_period_timestamps = st.lists(
        st.integers(min_value=2, max_value=PERIOD_CHECK_DURATION),
        unique=True,
        min_size=5,
        max_size=5,
    ).map(sorted)
    st_iterate_over_period = st_period_timestamps.map(
        lambda lst: [0, 1] + list(map(lambda x: x[1] - x[0], zip([0] + lst, lst + [PERIOD_CHECK_DURATION])))
    )  # generates ts_delta

    def __init__(self, crvusd, scrvusd, admin, soracle, verifier, soracle_slots, max_acceleration):
        super().__init__(crvusd, scrvusd, admin, soracle, verifier, soracle_slots)

        self.max_acceleration = max_acceleration / 10 ** 18

    @invariant(check_during_init=True)
    @given(data=st.data())
    def smoothed_price(self, data):
        """
        Test that price moves within limits set.
        """
        for get_soracle_price in [
            getattr(self.soracle, price_fn) for price_fn in [
                "price_v0",
                "price_v1",
                # "price_v2",
            ]
        ]:
            with boa.env.anchor():
                prev_price, prev_ts = get_soracle_price(), boa.env.evm.patch.timestamp
                for ts_delta in data.draw(self.st_iterate_over_period):
                    boa.env.time_travel(seconds=ts_delta)
                    new_price, new_ts = get_soracle_price(), boa.env.evm.patch.timestamp
                    # In fact, linear approximation is strictly less except new_ts - prev_ts == 1
                    assert (new_price / prev_price) <= (1. + self.max_acceleration) ** (new_ts - prev_ts)
                    prev_price, prev_ts = new_price, new_ts


@pytest.fixture(scope="module", params=[10 ** 11, 10 ** 12, 10 ** 13])
def max_acceleration(soracle, admin, request):
    with boa.env.prank(admin):
        soracle.set_max_acceleration(request.param)
    return request.param


@pytest.mark.slow
def test_scrvusd_oracle(crvusd, scrvusd, admin, max_acceleration, soracle, soracle_price_slots, verifier):
    run_state_machine_as_test(
        functools.partial(
            SmootheningStateMachine,
            # ScrvusdStateMachine
            crvusd=crvusd,
            scrvusd=scrvusd,
            admin=admin,
            # SoracleStateMachine
            soracle=soracle,
            verifier=verifier,
            soracle_slots=soracle_price_slots,
            # Smoothening test
            max_acceleration=max_acceleration,
        ),
        settings=settings(
            max_examples=10,
            stateful_step_count=10,
            deadline=None,
        )
    )
