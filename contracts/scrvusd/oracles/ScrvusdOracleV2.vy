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

version: public(constant(String[8])) = "0.2.0"


################################################################
#                            MODULES                           #
################################################################

from snekmate.auth import ownable

initializes: ownable
exports: ownable.__interface__


################################################################
#                            EVENTS                            #
################################################################

event PriceUpdate:
    new_price: uint256  # price to achieve
    price_params_ts: uint256  # timestamp at which price is recorded


event SetVerifier:
    verifier: address


################################################################
#                           CONSTANTS                          #
################################################################


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


################################################################
#                            STORAGE                           #
################################################################


verifier: public(address)

last_block_number: public(uint256)

# smoothening
last_prices: uint256[2]
last_update: uint256

# scrvusd replication parameters
price_params: uint256[ALL_PARAM_CNT]
price_params_ts: uint256

# vault_params_array: public(VaultParams)

# struct VaultParams:
#     timestamp: uint256
#     total_debt: uint256
#     total_idle: uint256
#     totalSupply: uint256
#     full_profit_unlock_date: uint256
#     profit_unlocking_rate: uint256
#     last_profit_update: uint256
#     balance_of_self: uint256


################################################################
#                          CONSTRUCTOR                         #
################################################################


@deploy
def __init__(_initial_price: uint256):
    """
    @param _initial_price Initial price of asset per share (10**18)
    """
    # self.last_prices = [_initial_price, _initial_price]
    self.last_update = block.timestamp

    # initial raw_price is 1
    self.price_params[0] = 1  # totalAssets = 1
    self.price_params[2] = 1  # totalSupply = 1

    ownable.__init__()


################################################################
#                    PERMISSIONED FUNCTIONS                    #
################################################################


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

    # update last_prices with previous parameters
    # self.last_prices = [self._price_v0(), self._price_v1()]
    self.last_update = block.timestamp

    current_price: uint256 = self._raw_price(self.price_params_ts)
    self.price_params = _parameters
    self.price_params_ts = _ts

    updated_price: uint256 = self._raw_price(_ts)
    # price is non-decreasing
    assert current_price <= updated_price, "Outdated"

    log PriceUpdate(updated_price, _ts)
    # return relative price change, because we want to know how big was a change
    # for autiomated actions rewards calculation
    return updated_price * 10**18 // current_price


@external
def set_verifier(_verifier: address):
    """
    @notice Set the account with verifier permissions.
    """
    ownable._check_owner()

    self.verifier = _verifier
    log SetVerifier(_verifier)


################################################################
#                         VIEW FUNCTIONS                       #
################################################################


@view
@external
def raw_price(_ts: uint256 = block.timestamp, _mode: uint256 = 0) -> uint256:
    """
    @notice Get approximate `scrvUSD.pricePerShare()` without smoothing
    @param _ts Timestamp at which to see price (only near period is supported)
    @param _mode 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return (self._raw_price(_ts) if _mode == 0 else 10**36 // self._raw_price(_ts))


@view
@external
def filtered_price(_ts: uint256 = block.timestamp, _mode: uint256 = 0) -> uint256:
    """
    @notice Get predicted price value assuming updates did not happen recently
    @param _ts Timestamp at which to see get the price
    @param _mode 0 (default) for `pricePerShare()` and 1 for `pricePerAsset()`
    """
    return (self._filtered_price(_ts) if _mode == 0 else 10**36 // self._filtered_price(_ts))


################################################################
#                        INTERNAL LOGIC                        #
################################################################


@view
@internal
def _filtered_price(_ts: uint256 = block.timestamp) -> uint256:
    """
    @dev
    """
    # params expiry is full_profit_unlock_date
    params_expiry_time: uint256 = self.price_params[ASSETS_PARAM_CNT + 1]
    last_profit_update: uint256 = self.price_params[ASSETS_PARAM_CNT + 3]
    # if we are within unlocking period, we use raw_price
    if _ts <= params_expiry_time:
        return self._raw_price(_ts)
    # if we are outside we use approximate future prediction based on previous data
    elif params_expiry_time != 0:  # excluding the case of oraclized params without rewards drip
        t_init: uint256 = last_profit_update
        price_init: uint256 = self._raw_price(t_init)

        t_fin: uint256 = params_expiry_time
        price_fin: uint256 = self._raw_price(t_fin)

        growth_rate: uint256 = 10**18 * (price_fin - price_init) // (t_fin - t_init)

        predicted_price: uint256 = price_fin + growth_rate * (_ts - t_fin) // 10**18
        return predicted_price
    else:
        return self._raw_price(_ts)


@view
@internal
def _raw_price(ts: uint256) -> uint256:
    """
    @notice Price replication from scrvUSD vault
    """
    parameters: uint256[ALL_PARAM_CNT] = self.price_params
    return self._total_assets(parameters) * 10**18 // self._total_supply(parameters, ts)


@view
@internal
def _total_assets(parameters: uint256[ALL_PARAM_CNT]) -> uint256:
    """
    @notice Total amount of assets that are in the vault and in the strategies.
    """
    # return self.total_idle + self.total_debt
    return parameters[0] + parameters[1]


@view
@internal
def _total_supply(parameters: uint256[ALL_PARAM_CNT], ts: uint256) -> uint256:
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
@internal
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
        unlocked_shares = (profit_unlocking_rate * (ts - last_profit_update) // MAX_BPS_EXTENDED)
    elif full_profit_unlock_date != 0:
        # All shares have been unlocked
        unlocked_shares = balance_of_self
    return unlocked_shares
