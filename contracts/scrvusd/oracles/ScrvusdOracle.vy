# pragma version 0.4.0
"""
@title scrvUSD oracle
@notice Oracle of scrvUSD share price for StableSwap pool and other integrations.
    Price updates are linearly smoothed with max acceleration to eliminate sharp changes.
@license MIT
@author curve.fi
@custom:version 0.0.1
@custom:security security@curve.fi
"""

version: public(constant(String[8])) = "0.0.1"

from snekmate.auth import ownable

initializes: ownable
exports: ownable.__interface__


event PriceUpdate:
    new_price: uint256  # price to achieve
    at: uint256  # timestamp at which price will be achieved


event SetProver:
    prover: address


struct Interval:
    previous: uint256
    future: uint256


# scrvUSD Vault rate replication
# 0 total_debt
# 1 total_idle
ASSETS_PARAM_CNT: constant(uint256) = 2
# 0 totalSupply
# 1 full_profit_unlock_date
# 2 profit_unlocking_rate
# 3 last_profit_update
# 4 balance_of_self
SUPPLY_PARAM_CNT: constant(uint256) = 5
MAX_BPS_EXTENDED: constant(uint256) = 1_000_000_000_000

prover: public(address)

price: public(Interval)  # price of asset per share
time: public(Interval)

max_acceleration: public(uint256)  # precision 10**18


@deploy
def __init__(_initial_price: uint256, _max_acceleration: uint256):
    """
    @param _initial_price Initial price of asset per share (10**18)
    @param _max_acceleration Maximum acceleration (10**12)
    """
    self.price = Interval(previous=_initial_price, future=_initial_price)
    self.time = Interval(previous=block.timestamp, future=block.timestamp)

    self.max_acceleration = _max_acceleration

    ownable.__init__()


@view
@internal
def _price_per_share(ts: uint256) -> uint256:
    """
    @notice Using linear interpolation assuming updates are often enough
        for absolute difference \approx relative difference
    """
    price: Interval = self.price
    time: Interval = self.time
    if ts >= time.future:
        return price.future
    if ts <= time.previous:
        return price.previous
    return (price.previous * (time.future - ts) + price.future * (ts - time.previous)) // (
        time.future - time.previous
    )


@view
@external
def pricePerShare(ts: uint256 = block.timestamp) -> uint256:
    """
    @notice Get the price per share (pps) of the vault.
    @dev NOT precise. Price is smoothed over time to eliminate sharp changes.
    @param ts Timestamp to look price at. Only near future is supported.
    @return The price per share.
    """
    return self._price_per_share(ts)


@view
@external
def pricePerAsset(ts: uint256 = block.timestamp) -> uint256:
    """
    @notice Get the price per asset of the vault.
    @dev NOT precise. Price is smoothed over time to eliminate sharp changes.
    @param ts Timestamp to look price at. Only near future is supported.
    @return The price per share.
    """
    return 10**36 // self._price_per_share(ts)


@view
@external
def price_oracle(i: uint256 = 0) -> uint256:
    """
    @notice Alias of `pricePerShare` and `pricePerAsset` made for compatability
    @param i 0 for scrvusd per crvusd, 1 for crvusd per scrvusd
    @return Price with 10^18 precision
    """
    return (
        self._price_per_share(block.timestamp)
        if i == 0
        else 10**36 // self._price_per_share(block.timestamp)
    )


@view
def _unlocked_shares(
    full_profit_unlock_date: uint256,
    profit_unlocking_rate: uint256,
    last_profit_update: uint256,
    balance_of_self: uint256,
    ts: uint256,
) -> uint256:
    """
    Returns the amount of shares that have been unlocked.
    To avoid sudden price_per_share spikes, profits can be processed
    through an unlocking period. The mechanism involves shares to be
    minted to the vault which are unlocked gradually over time. Shares
    that have been locked are gradually unlocked over profit_max_unlock_time.
    """
    unlocked_shares: uint256 = 0
    if full_profit_unlock_date > ts:
        # If we have not fully unlocked, we need to calculate how much has been.
        unlocked_shares = profit_unlocking_rate * (ts - last_profit_update) // MAX_BPS_EXTENDED

    elif full_profit_unlock_date != 0:
        # All shares have been unlocked
        unlocked_shares = balance_of_self

    return unlocked_shares


@view
def _total_supply(parameters: uint256[ASSETS_PARAM_CNT + SUPPLY_PARAM_CNT], ts: uint256) -> uint256:
    # Need to account for the shares issued to the vault that have unlocked.
    # return self.total_supply - self._unlocked_shares()
    return parameters[ASSETS_PARAM_CNT + 0] - self._unlocked_shares(
        parameters[ASSETS_PARAM_CNT + 1],  # full_profit_unlock_date
        parameters[ASSETS_PARAM_CNT + 2],  # profit_unlocking_rate
        parameters[ASSETS_PARAM_CNT + 3],  # last_profit_update
        parameters[ASSETS_PARAM_CNT + 4],  # balance_of_self
        ts,  # block.timestamp
    )


@view
def _total_assets(parameters: uint256[ASSETS_PARAM_CNT + SUPPLY_PARAM_CNT]) -> uint256:
    """
    @notice Total amount of assets that are in the vault and in the strategies.
    """
    # return self.total_idle + self.total_debt
    return parameters[0] + parameters[1]


@external
def update_price(
    _parameters: uint256[ASSETS_PARAM_CNT + SUPPLY_PARAM_CNT],
    _ts: uint256,
) -> uint256:
    """
    @notice Update price using `_parameters`
    @param _parameters Parameters of Yearn Vault to calculate scrvUSD price
    @param _ts Timestamp at which these parameters are true
    @return Relative price change of final price with 10^18 precision
    """
    assert msg.sender == self.prover

    current_price: uint256 = self._price_per_share(block.timestamp)
    new_price: uint256 = self._total_assets(_parameters) * 10**18 // self._total_supply(
        _parameters, _ts
    )

    # Price is always growing and updates are never from future,
    # hence allow only increasing updates
    future_price: uint256 = self.price.future
    if new_price > future_price:
        self.price = Interval(previous=current_price, future=new_price)

        rel_price_change: uint256 = (
            new_price - current_price
        ) * 10**18 // current_price + 1  # 1 for rounding up
        future_ts: uint256 = block.timestamp + rel_price_change // self.max_acceleration
        self.time = Interval(previous=block.timestamp, future=future_ts)

        log PriceUpdate(new_price, future_ts)
        return new_price * 10**18 // future_price
    return 10**18


@external
def set_max_acceleration(_max_acceleration: uint256):
    """
    @notice Set maximum acceleration of scrvUSD.
        Must be less than StableSwap's minimum fee.
        fee / (2 * block_time) is considered to be safe.
    @param _max_acceleration Maximum acceleration (per sec)
    """
    ownable._check_owner()

    assert 10**8 <= _max_acceleration and _max_acceleration <= 10**18
    self.max_acceleration = _max_acceleration


@external
def set_prover(_prover: address):
    """
    @notice Set the account with prover permissions.
    """
    ownable._check_owner()

    self.prover = _prover
    log SetProver(_prover)
