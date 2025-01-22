# pragma version 0.4.0
"""
@title scrvUSD oracle
@notice Oracle of scrvUSD share price for StableSwap pool and other integrations.
    Price updates are linearly smoothed with max acceleration to eliminate sharp changes.
@license MIT
@author curve.fi
@custom:version 0.1.0
@custom:security security@curve.fi
"""

version: public(constant(String[8])) = "0.1.0"

from snekmate.auth import ownable

initializes: ownable
exports: ownable.__interface__

event PriceUpdate:
    new_price: uint256  # price to achieve
    price_params_ts: uint256  # timestamp at which price is recorded
    block_number: uint256

event SetVerifier:
    verifier: address

event SetMaxAcceleration:
    max_acceleration: uint256


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
ALL_PARAM_CNT: constant(uint256) = ASSETS_PARAM_CNT + SUPPLY_PARAM_CNT
MAX_BPS_EXTENDED: constant(uint256) = 1_000_000_000_000

verifier: public(address)

last_block_number: public(uint256)
# smoothening
last_prices: uint256[2]
last_update: uint256
# scrvusd replication parameters
price_params: uint256[ALL_PARAM_CNT]
price_params_ts: uint256

max_acceleration: public(uint256)  # precision 10**18


@deploy
def __init__(_initial_price: uint256, _max_acceleration: uint256):
    """
    @param _initial_price Initial price of asset per share (10**18)
    @param _max_acceleration Maximum acceleration (10**12)
    """
    self.last_prices = [_initial_price, _initial_price]
    self.last_update = block.timestamp

    # initial raw_price is 1
    self.price_params[0] = 1  # totalAssets = 1
    self.price_params[2] = 1  # totalSupply = 1

    self.max_acceleration = _max_acceleration

    ownable.__init__()


@view
@external
def price_v0(_i: uint256=0) -> uint256:
    """
    @notice Get lower bound of `scrvUSD.pricePerShare()`
    @dev Price is updated in steps, need to verify every % changed
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return self._price_v0() if _i == 0 else 10**36 // self._price_v0()


@view
@external
def price_v1(_i: uint256=0) -> uint256:
    """
    @notice Get approximate `scrvUSD.pricePerShare()`
    @dev Price is simulated as if noone interacted to change `scrvUSD.pricePerShare()`,
        need to adjust rate when too off.
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return self._price_v1() if _i == 0 else 10**36 // self._price_v1()


@view
@external
def raw_price(_i: uint256=0, _ts: uint256=block.timestamp) -> uint256:
    """
    @notice Get approximate `scrvUSD.pricePerShare()` without smoothening
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    @param _ts Timestamp at which to see price (only near period is supported)
    """
    return self._raw_price(_ts) if _i == 0 else 10**36 // self._raw_price(_ts)


@view
def _smoothed_price(last_price: uint256, ts: uint256) -> uint256:
    raw_price: uint256 = self._raw_price(ts)
    max_change: uint256 = self.max_acceleration * (block.timestamp - self.last_update)
    # -max_change <= (raw_price - last_price) <= max_change
    if unsafe_sub(raw_price + max_change, last_price) > 2 * max_change:
        return last_price + max_change if raw_price > last_price else last_price - max_change
    return raw_price


@view
def _price_v0() -> uint256:
    return self._smoothed_price(self.last_prices[0], self.price_params_ts)


@view
def _price_v1() -> uint256:
    return self._smoothed_price(self.last_prices[1], block.timestamp)


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
def _total_supply(parameters: uint256[ALL_PARAM_CNT], ts: uint256) -> uint256:
    # Need to account for the shares issued to the vault that have unlocked.
    # return self.total_supply - self._unlocked_shares()
    return parameters[ASSETS_PARAM_CNT + 0] -\
        self._unlocked_shares(
            parameters[ASSETS_PARAM_CNT + 1],  # full_profit_unlock_date
            parameters[ASSETS_PARAM_CNT + 2],  # profit_unlocking_rate
            parameters[ASSETS_PARAM_CNT + 3],  # last_profit_update
            parameters[ASSETS_PARAM_CNT + 4],  # balance_of_self
            ts,  # block.timestamp
        )

@view
def _total_assets(parameters: uint256[ALL_PARAM_CNT]) -> uint256:
    """
    @notice Total amount of assets that are in the vault and in the strategies.
    """
    # return self.total_idle + self.total_debt
    return parameters[0] + parameters[1]


@view
def _raw_price(ts: uint256) -> uint256:
    """
    @notice Price replication from scrvUSD vault
    """
    parameters: uint256[ALL_PARAM_CNT] = self.price_params
    return self._total_assets(parameters) * 10 ** 18 // self._total_supply(parameters, ts)


@external
def update_price(_parameters: uint256[ALL_PARAM_CNT], _ts: uint256, _block_number: uint256) -> uint256:
    """
    @notice Update price using `_parameters`
    @param _parameters Parameters of Yearn Vault to calculate scrvUSD price
    @param _ts Timestamp at which these parameters are true
    @param _block_number Block number of parameters to linearize updates
    @return Relative price change of final price with 10^18 precision
    """
    assert msg.sender == self.verifier
    # Allowing same block updates for fixing bad blockhash provided (if possible)
    assert self.last_block_number <= _block_number, "Outdated"
    self.last_block_number = _block_number

    self.last_prices = [self._price_v0(), self._price_v1()]
    self.last_update = block.timestamp

    current_price: uint256 = self._raw_price(self.price_params_ts)
    self.price_params = _parameters
    self.price_params_ts = _ts

    new_price: uint256 = self._raw_price(_ts)
    log PriceUpdate(new_price, _ts, _block_number)
    return new_price * 10 ** 18 // current_price


@external
def set_max_acceleration(_max_acceleration: uint256):
    """
    @notice Set maximum acceleration of scrvUSD.
        Must be less than StableSwap's minimum fee.
        fee / (2 * block_time) is considered to be safe.
    @param _max_acceleration Maximum acceleration (per sec)
    """
    ownable._check_owner()

    assert 10 ** 8 <= _max_acceleration and _max_acceleration <= 10 ** 18
    self.max_acceleration = _max_acceleration

    log SetMaxAcceleration(_max_acceleration)


@external
def set_verifier(_verifier: address):
    """
    @notice Set the account with verifier permissions.
    """
    ownable._check_owner()

    self.verifier = _verifier
    log SetVerifier(_verifier)
