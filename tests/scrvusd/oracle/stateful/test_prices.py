import functools

import boa
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import invariant, run_state_machine_as_test, given
from tests.conftest import WEEK

from tests.scrvusd.oracle.stateful.crvusd_state_machine import SoracleStateMachine
import pytest


class SoracleTestStateMachine(SoracleStateMachine):
    """
    State Machine to test different oracle price versions behaviour.
    """

    # Tests become extremely slow (~7 min for test_price_simple)
    # Tried to use as:
    # @given(data=st.data())
    # def ...
    #       ...data.draw(self.st_time_delay)...
    #
    # st_week_timestamps = st.lists(
    #     st.integers(min_value=0, max_value=7 * 86400 - 1),
    #     unique=True,
    #     min_size=5,  # making execution time more determined
    #     max_size=5,
    # ).map(sorted)
    # st_iterate_over_week = st_week_timestamps.map(
    #     lambda lst: list(map(lambda x: x[1] - x[0], zip([0] + lst, lst + [7 * 86400])))
    # )  # generates ts_delta
    #
    # st_time_delay = st.integers(min_value=1, max_value=30 * 86400)
    #
    # st_weeks = st.lists(
    #     st.integers(min_value=1, max_value=4 * 3),
    #     unique=True,
    #     min_size=5,  # making execution time more determined
    #     max_size=5,
    # ).map(sorted)

    st_week_timestamps = [1, 60, 3600, 86400, 4 * 86400]
    st_iterate_over_week = [
        x[1] - x[0] for x in zip([0] + st_week_timestamps, st_week_timestamps + [7 * 86400])
    ]

    st_time_delays = [1, 86400, 3600, 30 * 86400, 60]
    st_weeks = [0, 1, 2, 5, 10, 12]

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
    def price_v1(self):
        """
        Test that v1 replicates the price function with no further updates of scrvUSD.

        Properties:
            - True if scrvUSD is not touched at all.
        """
        with boa.env.anchor():
            self.update_price()

            # Check following week
            for ts_delta in self.st_iterate_over_week:
                boa.env.time_travel(seconds=ts_delta)
                assert self.soracle.price_v1() == self.price()
            # Check random 10 timestamps after
            for delay in self.st_time_delays:
                boa.env.time_travel(seconds=delay)
                assert self.soracle.price_v1() == self.price()

    @invariant()
    @given(amount=st.integers(min_value=0, max_value=10**9 * 10**18))
    def price_v2(self, amount):
        self._price_v2(amount)

    def _price_v2(self, amount):
        """
        Test that v2 assumes same reward amount coming every week
        :param amount: Amount of rewards (in crvUSD) being distributed every week
        """
        # Check literally rewarding same amount at the start of every week
        with boa.env.anchor():
            # Forget about previous rewards
            boa.env.time_travel(seconds=7 * 86400)
            self.add_rewards(amount)
            self.update_price()

            for i in range(max(self.st_weeks)):
                if i in self.st_weeks:
                    for ts_delta in self.st_iterate_over_week:
                        boa.env.time_travel(seconds=ts_delta)
                        assert self.soracle.price_v2() == pytest.approx(
                            self.price(), rel=1e-8
                        )  # computation errors
                else:
                    boa.env.time_travel(seconds=7 * 86400)
                self.add_rewards(amount)

        # Simulate same total amount, but approximate price value
        with boa.env.anchor():
            amounts = [amount // 2, amount // 3]
            amounts.append(amount - sum(amounts))
            week_checkpoints = [0, 86400, 4 * 86400, 7 * 86400]
            sim_start = boa.env.evm.patch.timestamp

            # Last week
            price_change = self._get_final_price()
            for j in range(len(amounts)):
                self.add_rewards(amounts[j])
                j += 1
                boa.env.time_travel(
                    seconds=week_checkpoints[j] - (boa.env.evm.patch.timestamp - sim_start) % WEEK
                )
            price_change = self._get_final_price() / price_change
            self.update_price()
            self.soracle.price_v2()

            for i in range(max(self.st_weeks)):
                j = 0
                if i in self.st_weeks:
                    for ts_delta in self.st_iterate_over_week:
                        while (boa.env.evm.patch.timestamp - sim_start) % WEEK >= week_checkpoints[
                            j
                        ]:
                            self.add_rewards(amounts[j])
                            j += 1
                        boa.env.time_travel(seconds=ts_delta)
                        assert self.soracle.price_v2() == pytest.approx(
                            self.price(), rel=price_change
                        )
                while j < len(amounts):
                    self.add_rewards(amounts[j])
                    j += 1
                    boa.env.time_travel(
                        seconds=week_checkpoints[j]
                        - (boa.env.evm.patch.timestamp - sim_start) % WEEK
                    )

    def _get_final_price(self):
        total_idle = boa.env.evm.get_storage(self.scrvusd.address, self.soracle_slots[1])
        total_supply = boa.env.evm.get_storage(self.scrvusd.address, self.soracle_slots[2])
        balance_of_self = boa.env.evm.get_storage(self.scrvusd.address, self.soracle_slots[6])
        return total_idle * 10**18 // (total_supply - balance_of_self)


@pytest.fixture(scope="module", autouse=True)
def max_acceleration(soracle, admin):
    """
    Turning off smoothening.
    """
    # big enough to be omitted in calculation and
    # small enough not to overflow
    max_acceleration = 2**128 - 1
    soracle.eval(f"self.max_acceleration = {max_acceleration}")
    return max_acceleration


def test_price_simple(crvusd, scrvusd, admin, soracle, soracle_price_slots, verifier):
    machine = SoracleTestStateMachine(
        # ScrvusdStateMachine
        crvusd=crvusd,
        scrvusd=scrvusd,
        admin=admin,
        # SoracleStateMachine
        soracle=soracle,
        verifier=verifier,
        soracle_slots=soracle_price_slots,
    )
    machine.price_v0()
    machine.price_v1()
    machine._price_v2(333 * 10**18)

    machine.user_changes(4444 * 10**18)
    machine.wait(3600)
    machine.price_v0()
    machine.price_v1()
    machine._price_v2(333 * 10**18)

    machine.add_rewards(22 * 10**18)
    machine.wait(1800)
    machine.price_v0()
    machine.price_v1()
    machine._price_v2(333 * 10**18)


def test_period_not_full(crvusd, scrvusd, admin, soracle, soracle_price_slots, verifier):
    # full_profit_unlock_date can be < last_profit_update + profit_max_unlock_time
    state = SoracleTestStateMachine(
        # ScrvusdStateMachine
        crvusd=crvusd,
        scrvusd=scrvusd,
        admin=admin,
        # SoracleStateMachine
        soracle=soracle,
        verifier=verifier,
        soracle_slots=soracle_price_slots,
    )
    state.update_price()
    state._price_v2(2)


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
        ),
    )
