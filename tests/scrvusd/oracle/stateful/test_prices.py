import functools
from datetime import timedelta

import boa
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import invariant, run_state_machine_as_test, given

from tests.scrvusd.oracle.stateful.crvusd_state_machine import SoracleStateMachine
import pytest


class SoracleTestStateMachine(SoracleStateMachine):
    """
    State Machine to test different oracle price versions behaviour.
    """

    st_week_timestamps = st.lists(
        st.integers(min_value=1, max_value=7 * 86400),
        unique=True,
        min_size=5,  # making time
        max_size=5,
    ).map(sorted)
    st_iterate_over_week = st_week_timestamps.map(
        lambda lst: list(map(lambda x: x[1] - x[0], zip([0] + lst, lst + [7 * 86400])))
    )  # generates ts_delta

    st_time_delay = st.integers(min_value=1, max_value=30 * 86400)

    def __init__(self, crvusd, scrvusd, admin, soracle, verifier, soracle_slots):
        super().__init__(crvusd, scrvusd, admin, soracle, verifier, soracle_slots)

        self.last_oracle_v0 = self.soracle.price_v0()

    @invariant()
    def raw_price(self):
        """
        Test that `update_price(...)` catches up the price.
        """
        with boa.env.anchor():
            self.update_price()
            assert self.soracle.raw_price() == self.price()

    @invariant()
    def price_v0(self):
        """
        Test that v0 is increasing towards the price and does not exceed it.

        Properties:
            - Non-decreasing.
            - Does not exceed real price.
            - Fetches the price up to "fetch" timestamp.
        """
        cur_price = self.soracle.price_v0()
        assert self.last_oracle_v0 <= cur_price <= self.price()
        self.last_oracle_v0 = cur_price

        with boa.env.anchor():
            self.update_price()
            # Update comes only the next second, but the actual price might change the next second
            price = self.price()
            boa.env.time_travel(seconds=1)
            assert self.soracle.price_v0() == price

    @invariant()
    @given(data=st.data())
    def price_v1(self, data):
        """
        Test that v1 replicates the price function with no further updates of scrvUSD.

        Properties:
            - True if scrvUSD is not touched at all.
        """
        with boa.env.anchor():
            self.update_price()

            # Check following week
            for ts_delta in data.draw(self.st_iterate_over_week):
                boa.env.time_travel(seconds=ts_delta)
                assert self.soracle.price_v1() == self.price()
            # Check random 10 timestamps after
            for _ in range(10):
                boa.env.time_travel(seconds=data.draw(self.st_time_delay))
                assert self.soracle.price_v1() == self.price()

    # @invariant()
    # @given(amount=st.integers(min_value=0, max_value=10 ** 9 * 10 ** 18))
    # @given(data=st.data())
    # def price_v2(self, data, amount):
    #     """
    #     Test that v2 assumes same reward amount coming every week
    #     :param amount: Amount of rewards (in crvUSD) being distributed every week
    #     """
    #     # Check literally rewarding same amount at the start of every week
    #     with boa.env.anchor():
    #         # Forget about previous rewards
    #         boa.env.time_travel(seconds=7 * 86400)
    #         self.add_rewards(amount)
    #         self.process_rewards()
    #         self.update_price()
    #
    #         weeks_to_check = data.draw(self.st_weeks)
    #         for i in range(max(*weeks_to_check)):
    #             self.add_rewards(amount)
    #             self.process_rewards()
    #
    #             if i in weeks_to_check:
    #                 for ts_delta in data.draw(self.st_iterate_over_week):
    #                     boa.env.time_travel(seconds=ts_delta)
    #                     assert self.soracle.price_v2() == self.price()
    #             else:
    #                 boa.env.time_travel(seconds=7 * 86400)
    #
    #     # Simulate same total amount, but approximate price value
    #     with boa.env.anchor():
    #         pass


@pytest.fixture(scope="module", autouse=True)
def max_acceleration(soracle, admin):
    """
    Turning off smoothening.
    """
    # big enough to be omitted in calculation and
    # small enough not to overflow
    max_acceleration = 2 ** 128 - 1
    soracle.eval(f"self.max_acceleration = {max_acceleration}")
    return max_acceleration


@pytest.mark.slow
def test_scrvusd_oracle(crvusd, scrvusd, admin, soracle, soracle_price_slots, verifier):
    run_state_machine_as_test(
        functools.partial(
            SoracleTestStateMachine,
            # ScrvusdStateMachine
            crvusd=crvusd,
            scrvusd=scrvusd,
            admin=admin,
            # SoracleStateMachine
            soracle=soracle,
            verifier=verifier,
            soracle_slots=soracle_price_slots,
        ),
        settings=settings(
            max_examples=10,
            stateful_step_count=10,
            deadline=None,
        )
    )
