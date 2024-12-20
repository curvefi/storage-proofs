import boa
import time

# scrvUSD Vault rate replication
# 0 total_debt
# 1 total_idle
# 2 totalSupply
# 3 full_profit_unlock_date
# 4 profit_unlocking_rate
# 5 last_profit_update
# 6 balance_of_self


def test_default_behavior(scrvusd_rate_oracle, verifier_mock):
    ts = int(time.time())
    params_array = [
        0,  # total_debt
        10_000 * 10**18,  # total_idle
        10_000 * 10**18,  # totalSupply
        ts + 200,  # full_profit_unlock_date
        1 * 10 ** (18 + 12),  # profit_unlocking_rate
        ts,  # last_profit_update
        100 * 10**18,  # balance of self (to be accounted as rewards and change the price)
    ]  # balance_of_self
    with boa.env.prank(verifier_mock):
        scrvusd_rate_oracle.update_price(params_array, ts)

    # price at period beginning must be 1
    assert scrvusd_rate_oracle.raw_price(ts) == 10**18
    assert scrvusd_rate_oracle.raw_price(ts + 100) == int(10**18 * 10_000 // (10_000 - 100))
    # # # price at period end must be +100 * 10**18
    # assert scrvusd_rate_oracle.raw_price(ts + 100000) == 10100 / 10000 * 10**18
