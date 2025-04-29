# pragma version 0.4.0
"""
@title scrvUSD oracle
@notice Oracle of scrvUSD share price for StableSwap pool and other integrations.
    Price updates are linearly smoothed with max acceleration to eliminate sharp changes.
    Supports 2 types of approximation: assuming no changes through 1 rewards period and several periods with equal gains.
@license MIT
@author curve.fi
@custom:version 2.0.0
@custom:security security@curve.fi
"""

version: public(constant(String[8])) = "2.0.0"

from snekmate.auth import access_control

initializes: access_control
exports: (
    access_control.supportsInterface,
    access_control.hasRole,
    access_control.DEFAULT_ADMIN_ROLE,
    access_control.grantRole,
    access_control.revokeRole,
)


event PriceUpdate:
    new_price: uint256  # price to achieve
    price_params_ts: uint256  # timestamp at which price is recorded
    block_number: uint256


event SetMaxPriceIncrement:
    max_acceleration: uint256


event SetMaxV2Duration:
    max_v2_duration: uint256


event NewProfitMaxUnlockTime:
    profit_max_unlock_time: uint256


struct PriceParams:
    # assets
    total_debt: uint256
    total_idle: uint256
    # supply
    total_supply: uint256
    full_profit_unlock_date: uint256
    profit_unlocking_rate: uint256
    last_profit_update: uint256
    balance_of_self: uint256


# scrvUSD Vault rate replication
ALL_PARAM_CNT: constant(uint256) = 2 + 5
MAX_BPS_EXTENDED: constant(uint256) = 1_000_000_000_000

MAX_V2_DURATION: constant(uint256) = 4 * 12 * 4  # 4 years

PRICE_PARAMETERS_VERIFIER: public(constant(bytes32)) = keccak256("PRICE_PARAMETERS_VERIFIER")
UNLOCK_TIME_VERIFIER: public(constant(bytes32)) = keccak256("UNLOCK_TIME_VERIFIER")

last_block_number: public(uint256)  # Warning: used both for price parameters and unlock_time
# smoothening
last_prices: uint256[3]
last_update: uint256
# scrvUSD replication parameters
profit_max_unlock_time: public(uint256)
price_params: PriceParams
price_params_ts: uint256

max_price_increment: public(uint256)  # precision 10**18
max_v2_duration: public(uint256)  # number of periods(weeks)


@deploy
def __init__(_initial_price: uint256):
    """
    @param _initial_price Initial price of asset per share (10**18)
    """
    self.last_prices = [_initial_price, _initial_price, _initial_price]
    self.last_update = block.timestamp

    # initial raw_price is 1
    self.profit_max_unlock_time = 7 * 86400  # Week by default
    self.price_params = PriceParams(
        total_debt=0,
        total_idle=_initial_price,
        total_supply=10**18,
        full_profit_unlock_date=0,
        profit_unlocking_rate=0,
        last_profit_update=0,
        balance_of_self=0,
    )
    log NewProfitMaxUnlockTime(self.profit_max_unlock_time)

    # 2 * 10 ** 12 is equivalent to
    #   1) 0.02 bps per second or 0.24 bps per block on Ethereum
    #   2) linearly approximated to max 63% APY
    self.max_price_increment = 2 * 10**12
    self.max_v2_duration = 4 * 6  # half a year

    access_control.__init__()
    access_control._set_role_admin(PRICE_PARAMETERS_VERIFIER, access_control.DEFAULT_ADMIN_ROLE)
    access_control._set_role_admin(UNLOCK_TIME_VERIFIER, access_control.DEFAULT_ADMIN_ROLE)


@view
@external
def price_v0(_i: uint256 = 0) -> uint256:
    """
    @notice Get lower bound of `scrvUSD.pricePerShare()`
    @dev Price is updated in steps, need to verify every % changed
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return self._price_v0() if _i == 0 else 10**36 // self._price_v0()


@view
@external
def price_v1(_i: uint256 = 0) -> uint256:
    """
    @notice Get approximate `scrvUSD.pricePerShare()`
    @dev Price is simulated as if noone interacted to change `scrvUSD.pricePerShare()`,
        need to adjust rate when too off.
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return self._price_v1() if _i == 0 else 10**36 // self._price_v1()


@view
@external
def price_v2(_i: uint256 = 0) -> uint256:
    """
    @notice Get approximate `scrvUSD.pricePerShare()`
    @dev Uses assumption that crvUSD gains same rewards.
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return self._price_v2() if _i == 0 else 10**36 // self._price_v2()


@view
@external
def raw_price(
    _i: uint256 = 0, _ts: uint256 = block.timestamp, _parameters_ts: uint256 = block.timestamp
) -> uint256:
    """
    @notice Get approximate `scrvUSD.pricePerShare()` without smoothening
    @param _i 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    @param _ts Timestamp at which to see price (only near period is supported)
    """
    p: uint256 = self._raw_price(_ts, _parameters_ts)
    return p if _i == 0 else 10**36 // p


@view
def _smoothed_price(last_price: uint256, raw_price: uint256) -> uint256:
    # Ideally should be (max_price_increment / 10**18) ** (block.timestamp - self.last_update)
    # Using linear approximation to simplify calculations
    max_change: uint256 = (
        self.max_price_increment * (block.timestamp - self.last_update) * last_price // 10**18
    )
    # -max_change <= (raw_price - last_price) <= max_change
    if unsafe_sub(raw_price + max_change, last_price) > 2 * max_change:
        return last_price + max_change if raw_price > last_price else last_price - max_change
    return raw_price


@view
def _price_v0() -> uint256:
    return self._smoothed_price(
        self.last_prices[0],
        self._raw_price(self.price_params_ts, self.price_params.last_profit_update),
    )


@view
def _price_v1() -> uint256:
    return self._smoothed_price(
        self.last_prices[1], self._raw_price(block.timestamp, self.price_params_ts)
    )


@view
def _price_v2() -> uint256:
    return self._smoothed_price(
        self.last_prices[2], self._raw_price(block.timestamp, block.timestamp)
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
def _total_supply(p: PriceParams, ts: uint256) -> uint256:
    # Need to account for the shares issued to the vault that have unlocked.
    return p.total_supply - self._unlocked_shares(
        p.full_profit_unlock_date,
        p.profit_unlocking_rate,
        p.last_profit_update,
        p.balance_of_self,
        ts,  # block.timestamp
    )


@view
def _total_assets(p: PriceParams) -> uint256:
    """
    @notice Total amount of assets that are in the vault and in the strategies.
    """
    return p.total_idle + p.total_debt


@view
def _obtain_price_params(parameters_ts: uint256) -> PriceParams:
    """
    @notice Obtain Price parameters true or assumed to be true at `parameters_ts`.
        Assumes constant gain(in crvUSD rewards) through distribution periods.
    @param parameters_ts Timestamp to obtain parameters for
    @return Assumed `PriceParams`
    """
    params: PriceParams = self.price_params
    period: uint256 = self.profit_max_unlock_time
    if params.last_profit_update + period >= parameters_ts:
        return params

    number_of_periods: uint256 = min(
        (parameters_ts - params.last_profit_update) // period,
        self.max_v2_duration,
    )

    # locked shares at moment params.last_profit_update
    gain: uint256 = (
        params.balance_of_self * (params.total_idle + params.total_debt) // params.total_supply
    )
    params.total_idle += gain * number_of_periods

    # functions are reduced from `VaultV3._process_report()` given assumptions with constant gain
    for _: uint256 in range(number_of_periods, bound=MAX_V2_DURATION):
        new_balance_of_self: uint256 = (
            params.balance_of_self
            * (params.total_supply - params.balance_of_self) // params.total_supply
        )
        params.total_supply -= (
            params.balance_of_self * params.balance_of_self // params.total_supply
        )
        params.balance_of_self = new_balance_of_self

    if params.full_profit_unlock_date > params.last_profit_update:
        # copy from `VaultV3._process_report()`
        params.profit_unlocking_rate = params.balance_of_self * MAX_BPS_EXTENDED // (
            params.full_profit_unlock_date - params.last_profit_update
        )
    else:
        params.profit_unlocking_rate = 0

    params.full_profit_unlock_date += number_of_periods * period
    params.last_profit_update += number_of_periods * period

    return params


@view
def _raw_price(ts: uint256, parameters_ts: uint256) -> uint256:
    """
    @notice Price replication from scrvUSD vault
    """
    parameters: PriceParams = self._obtain_price_params(parameters_ts)
    return self._total_assets(parameters) * 10**18 // self._total_supply(parameters, ts)


@external
def update_price(
    _parameters: uint256[ALL_PARAM_CNT], _ts: uint256, _block_number: uint256
) -> uint256:
    """
    @notice Update price using `_parameters`
    @param _parameters Parameters of Yearn Vault to calculate scrvUSD price
    @param _ts Timestamp at which these parameters are true
    @param _block_number Block number of parameters to linearize updates
    @return Absolute relative price change of final price with 10^18 precision
    """
    access_control._check_role(PRICE_PARAMETERS_VERIFIER, msg.sender)
    # Allowing same block updates for fixing bad blockhash provided (if possible)
    assert self.last_block_number <= _block_number, "Outdated"
    self.last_block_number = _block_number

    self.last_prices = [self._price_v0(), self._price_v1(), self._price_v2()]
    self.last_update = block.timestamp

    ts: uint256 = self.price_params_ts
    current_price: uint256 = self._raw_price(ts, ts)
    self.price_params = PriceParams(
        total_debt=_parameters[0],
        total_idle=_parameters[1],
        total_supply=_parameters[2],
        full_profit_unlock_date=_parameters[3],
        profit_unlocking_rate=_parameters[4],
        last_profit_update=_parameters[5],
        balance_of_self=_parameters[6],
    )
    self.price_params_ts = _ts

    new_price: uint256 = self._raw_price(_ts, _ts)
    log PriceUpdate(new_price, _ts, _block_number)
    if new_price > current_price:
        return (new_price - current_price) * 10**18 // current_price
    return (current_price - new_price) * 10**18 // current_price


@external
def update_profit_max_unlock_time(_profit_max_unlock_time: uint256, _block_number: uint256) -> bool:
    """
    @notice Update price using `_parameters`
    @param _profit_max_unlock_time New `profit_max_unlock_time` value
    @param _block_number Block number of parameters to linearize updates
    @return Boolean whether value changed
    """
    access_control._check_role(UNLOCK_TIME_VERIFIER, msg.sender)
    # Allowing same block updates for fixing bad blockhash provided (if possible)
    assert self.last_block_number <= _block_number, "Outdated"
    self.last_block_number = _block_number

    prev_value: uint256 = self.profit_max_unlock_time
    self.profit_max_unlock_time = _profit_max_unlock_time
    log NewProfitMaxUnlockTime(_profit_max_unlock_time)
    return prev_value != _profit_max_unlock_time


@external
def set_max_price_increment(_max_price_increment: uint256):
    """
    @notice Set maximum price increment of scrvUSD.
        Must be less than StableSwap's minimum fee.
        fee / (2 * block_time) is considered to be safe.
    @param _max_price_increment Maximum acceleration (per sec)
    """
    access_control._check_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)

    assert 10**8 <= _max_price_increment and _max_price_increment <= 10**18
    self.max_price_increment = _max_price_increment

    log SetMaxPriceIncrement(_max_price_increment)


@external
def set_max_v2_duration(_max_v2_duration: uint256):
    """
    @notice Set maximum v2 approximation duration after which growth will be stopped.
    @param _max_v2_duration Maximum v2 approximation duration (in number of periods)
    """
    access_control._check_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)

    assert _max_v2_duration <= MAX_V2_DURATION
    self.max_v2_duration = _max_v2_duration

    log SetMaxV2Duration(_max_v2_duration)
