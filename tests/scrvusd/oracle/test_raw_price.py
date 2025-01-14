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
    distribution_time = 200
    full_profit_unlock_date = ts + distribution_time
    shares_to_distribute = 500 * 10**18
    profit_unlock_rate = 10**12 * (shares_to_distribute // 200)

    params_array = [
        0,  # total_debt
        10_000 * 10**18,  # total_idle
        10_000 * 10**18,  # totalSupply
        full_profit_unlock_date,  # full_profit_unlock_date
        profit_unlock_rate,  # profit_unlocking_rate
        ts,  # last_profit_update
        shares_to_distribute,  # balance of self (to be accounted as rewards and change the price)
    ]  # balance_of_self

    with boa.env.prank(verifier_mock):
        scrvusd_rate_oracle.update_price(params_array, ts, 1)

    # price at period beginning must be 1
    assert scrvusd_rate_oracle.raw_price(ts) == 10**18

    # as time passes, we must now have different price
    assert scrvusd_rate_oracle.raw_price(full_profit_unlock_date) == int(
        10**36 * 10_000 // (10_000 * 10**18 - shares_to_distribute)
    )

    # # test different mode (inverted price)
    assert scrvusd_rate_oracle.raw_price(full_profit_unlock_date, 1) == int(
        10**18 * (10_000 * 10**18 - shares_to_distribute) // (10_000 * 10**18)
    )
