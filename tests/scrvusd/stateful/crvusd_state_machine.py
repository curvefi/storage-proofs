import boa
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule


class ScrvusdStateMachine(RuleBasedStateMachine):

    st_crvusd_amount = st.integers(min_value=0, max_value=10 ** 36)
    st_time_delay = st.integers(min_value=0, max_value=365 * 86_400)

    def __init__(self, crvusd, scrvusd, admin):
        super().__init__()

        self.crvusd = crvusd
        self.scrvusd = scrvusd
        self.admin = admin

        self.user = boa.boa.env.generate_address()
        boa.env.eoa = self.user

        # premint
        self.crvusd._mint_for_testing(self.user, 10 ** (18 * 3))
        self.crvusd.approve(self.scrvusd, 2 ** 256 - 1)
        self.scrvusd.deposit(10**10, self.user)  # initial deposit with dust

    def price(self):
        return self.scrvusd.pricePerShare()

    @rule(supply=st.integers(min_value=10 ** 10, max_value=10 ** 36))
    def user_changes(self, supply):
        diff = supply - self.scrvusd.totalSupply()
        if diff > 0:
            self.scrvusd.mint(diff, self.user)
        elif diff < 0:
            self.scrvusd.redeem(-diff, self.user, self.user)

    @rule(amount=st_crvusd_amount)
    def add_rewards(self, amount):
        self.crvusd._mint_for_testing(self.scrvusd, amount)

    @rule()
    def process_rewards(self):
        with boa.env.prank(self.admin):
            self.scrvusd.process_report(self.scrvusd.address)

    @rule(time_delta=st_time_delay)
    def wait(self, time_delta):
        boa.env.time_travel(seconds=time_delta)
