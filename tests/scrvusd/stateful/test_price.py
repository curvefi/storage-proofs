import functools

import boa
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import invariant, rule, run_state_machine_as_test, given

from tests.scrvusd.stateful.crvusd_state_machine import ScrvusdStateMachine
import pytest


class SoracleTestStateMachine(ScrvusdStateMachine):

    st_week_timestamps = st.lists(
        st.integers(min_value=0, max_value=7 * 86400),
        unique=True,
        min_size=1,
        max_size=10,
    ).map(sorted)
    st_iterate_over_week = st_week_timestamps.map(
        lambda lst: list(map(lambda x: x[1] - x[0], zip([0] + lst, lst + [7 * 86400])))
    )  # generates ts_delta
    st_weeks = st.lists(
        st.integers(min_value=0, max_value=365 // 7 + 1),
        unique=True,
        min_size=1,
        max_size=10,
    ).map(sorted)

    def __init__(self, crvusd, scrvusd, admin, soracle, max_acceleration, verifier, soracle_slots):
        super().__init__(crvusd, scrvusd, admin)
        self.soracle = soracle
        self.max_acceleration = max_acceleration

        self.verifier = verifier
        self.soracle_slots = soracle_slots

    @rule()
    def update_price(self):
        with boa.env.prank(self.verifier):
            self.soracle.update_price(
                [
                    boa.env.evm.get_storage(self.scrvusd.address, slot)
                    for slot in self.soracle_slots
                ],
                boa.env.evm.patch.timestamp,
                boa.env.evm.patch.block_number,
            )

    @invariant()
    def raw_price_equality(self):
        """
        Test that `update_price(...)` catches up the price
        """
        with boa.env.anchor():
            self.update_price()
            assert self.soracle.raw_price() == self.price()

    def check_smoothening(self, last_price, last_ts, cur_price, cur_ts):
        assert (cur_price / last_price) <= (1. + self.max_acceleration) ** (cur_ts - last_ts)
        return cur_price, cur_ts

    @invariant(check_during_init=True)
    def price_v0(self):
        """
        Test that v0 is increasing towards the price and does not exceed it.
        """
        cur_price = self.soracle.price_v0()
        if not hasattr(self, "last_oracle_v0"):
            self.last_oracle_v0 = (cur_price, boa.env.evm.patch.timestamp)

        assert self.last_oracle_v0[0] <= cur_price <= self.price()
        self.last_oracle_v0 = self.check_smoothening(*self.last_oracle_v0, cur_price, boa.env.evm.patch.timestamp)

    @invariant(check_during_init=True)
    @given(data=st.data())
    def price_v1(self, data):
        """
        Test that v1 replicates the price function with no further updates of scrvUSD.
        """
        if not hasattr(self, "last_oracle_v1"):
            self.last_oracle_v1 = (self.soracle.price_v1(), boa.env.evm.patch.timestamp)
            return

        self.last_oracle_v1 = self.check_smoothening(
            *self.last_oracle_v1, self.soracle.price_v1(), boa.env.evm.patch.timestamp
        )
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
    # def price_v2(self):
    #     """
    #     Test that v2 assumes same reward amount coming every week
    #     """
    #     if not hasattr(self, "last_oracle_v2"):
    #         self.last_oracle_v2 = (self.soracle.price_v2(), boa.env.evm.patch.timestamp)
    #         return
    #     self.last_oracle_v2 = self.check_smoothening(
    #         *self.last_oracle_v2, self.soracle.price_v2(), boa.env.evm.patch.timestamp
    #     )
    #
    #     amount = self.st_crvusd_amount.example()
    #
    #     # Check literally rewarding same amount at the start of every week
    #     with boa.env.anchor():
    #         # Forget about previous rewards
    #         boa.env.time_travel(seconds=7 * 86400)
    #         self.add_rewards(amount)
    #         self.process_rewards()
    #         self.update_price()
    #
    #         weeks_to_check = self.st_weeks.example()
    #         for i in range(max(*weeks_to_check)):
    #             self.add_rewards(amount)
    #             self.process_rewards()
    #
    #             if i in weeks_to_check:
    #                 for ts_delta in self.st_iterate_over_week.example():
    #                     boa.env.time_travel(seconds=ts_delta)
    #                     assert self.soracle.price_v2() == self.price()
    #             else:
    #                 boa.env.time_travel(seconds=7 * 86400)
    #
    #     # Simulate same total amount, but approximate price value
    #     with boa.env.anchor():
    #         pass


@pytest.fixture(scope="module")
def verifier(soracle, admin):
    verifier = boa.env.generate_address()
    with boa.env.prank(admin):
        soracle.set_verifier(verifier)
    return verifier


def test_scrvusd_oracle(crvusd, scrvusd, admin, max_acceleration, soracle, soracle_slots, verifier):
    run_state_machine_as_test(
        functools.partial(
            SoracleTestStateMachine,
            # ScrvusdStateMachine
            crvusd=crvusd,
            scrvusd=scrvusd,
            admin=admin,
            # TestStateMachine
            soracle=soracle,
            max_acceleration=max_acceleration / 10 ** 18,
            verifier=verifier,
            soracle_slots=soracle_slots,
        ),
        settings=settings(
            max_examples=1,
            stateful_step_count=5,
        )
    )
