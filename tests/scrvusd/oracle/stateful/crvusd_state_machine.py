import boa
from hypothesis import strategies as st, settings
from hypothesis.stateful import RuleBasedStateMachine, rule


DUST_AMOUNT = 10 ** 10

settings.register_profile("default", settings(deadline=None))
settings.load_profile("default")


class ScrvusdStateMachine(RuleBasedStateMachine):
    """
    State Machine of different scrvUSD states.
    Assumptions:
        - The balance of scrvUSD will always maintain at least a 'DUST_AMOUNT'.
        - There are rewards streaming from the inception of scrvUSD.

    TODO: add set methods(unlock time, introducing debt value, etc) to be sure oracle will work under any circumstances.
    """

    def __init__(self, crvusd, scrvusd, admin):
        super().__init__()

        self.crvusd = crvusd
        self.scrvusd = scrvusd
        self.admin = admin

        self.user = boa.boa.env.generate_address()
        boa.env.eoa = self.user

        # premint and initial deposit
        self.crvusd._mint_for_testing(self.user, 10 ** (18 * 3))
        self.crvusd.approve(self.scrvusd, 2 ** 256 - 1)
        self.scrvusd.deposit(10**18, self.user)
        self.add_rewards(10 ** (18 - 3))

    def price(self):
        """
        :return: scrvUSD current price.
        """
        return self.scrvusd.pricePerShare()

    @rule(supply=st.integers(min_value=DUST_AMOUNT, max_value=10 ** 36))
    def user_changes(self, supply):
        """
        User crvUSD deposit/withdraw. Using scrvUSD supply parametrization to
            1) limit the final balance to stay within both upper and lower limits,
            2) merge subsequent deposit+withdraw into one.
        :param supply: Final users' scrvUSD supply (in shares).
        """
        diff = supply - self.scrvusd.balanceOf(self.user)
        if diff > 0:
            self.scrvusd.mint(diff, self.user)
        elif diff < 0:
            self.scrvusd.redeem(-diff, self.user, self.user)

    @rule(amount=st.integers(min_value=1, max_value=10 ** 9 * 10 ** 18))
    def add_rewards(self, amount):
        """
        Adding rewards like from FeeSplitter.
        :param amount: Amount in crvUSD.
        """
        self.crvusd._mint_for_testing(self.scrvusd, amount)
        # Since sending crvUSD does not alter scrvUSD contract's storage we can call both functions at once
        with boa.env.prank(self.admin):
            self.scrvusd.process_report(self.scrvusd.address)

    @rule(time_delta=st.integers(min_value=1, max_value=365 * 86_400))
    def wait(self, time_delta):
        """
        By default, time does not grow, so need to manually wait between operations.
        :param time_delta: Time in seconds.
        """
        boa.env.time_travel(seconds=time_delta)


class SoracleStateMachine(ScrvusdStateMachine):
    """
    State Machine of different scrvUSD oracle states.
    """

    def __init__(self, crvusd, scrvusd, admin, soracle, verifier, soracle_slots):
        super().__init__(crvusd, scrvusd, admin)
        self.soracle = soracle

        self.verifier = verifier
        self.soracle_slots = soracle_slots

    @rule()
    def update_price(self):
        """
        Simulate price update in oracle.
        """
        with boa.env.prank(self.verifier):
            self.soracle.update_price(
                [
                    boa.env.evm.get_storage(self.scrvusd.address, slot)
                    for slot in self.soracle_slots
                ],
                boa.env.evm.patch.timestamp,
                boa.env.evm.patch.block_number,
            )
