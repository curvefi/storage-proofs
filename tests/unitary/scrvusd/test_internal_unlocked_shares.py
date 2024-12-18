import boa
import time


def test_partial_unlock(oracle):
    """
    Test the `_unlocked_shares` function when shares are partially unlocked.
    """
    # Inputs
    full_profit_unlock_date = int(time.time() + 86_400)  # 1 day from now
    profit_unlocking_rate = 1_000 * 10**18 // (7 * 86_400)  # 1k shares per week
    last_profit_update = int(time.time() - 86_400)  # 1 day ago
    balance_of_self = 100_000 * 10**18  # 100k shares
    ts = int(time.time())  # now
    max_bps_extended = 1_000_000_000_000

    # Expected result
    expected_unlocked_shares = profit_unlocking_rate * (ts - last_profit_update) // max_bps_extended

    # Call the function
    result = oracle.eval(
        f"self._unlocked_shares({full_profit_unlock_date}, {profit_unlocking_rate}, {last_profit_update}, {balance_of_self}, {ts})"
    )
    # Assertions
    assert result == expected_unlocked_shares, f"Expected {expected_unlocked_shares}, got {result}"


def test_fully_unlocked(oracle):
    """
    Test the `_unlocked_shares` function when all shares are fully unlocked.
    """
    # Inputs
    full_profit_unlock_date = int(time.time() - 86_400)  # 1 day ago (fully unlocked)
    profit_unlocking_rate = 1_000 * 10**18 // (7 * 86_400)  # 1k shares per week
    last_profit_update = int(time.time() - 2 * 86_400)  # 2 days ago
    balance_of_self = 100_000 * 10**18  # 100k shares
    ts = int(time.time())  # now

    # Expected result
    expected_unlocked_shares = balance_of_self

    # Call the function
    result = oracle.eval(
        f"self._unlocked_shares({full_profit_unlock_date}, {profit_unlocking_rate}, {last_profit_update}, {balance_of_self}, {ts})"
    )

    # Assertions
    assert result == expected_unlocked_shares, f"Expected {expected_unlocked_shares}, got {result}"
