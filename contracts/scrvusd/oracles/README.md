## V0
Something like _read price from Ethereum_.
**Known issues**:
- Smoothening is not scaled to current price

## V1
Simulates price for ongoing period.
`max_acceleration` was renamed to `max_price_increment`

## V2
Simulates equal gain over periods.

### Alternative version
Not tested
```vyper
@view
def _obtain_price_params(parameters_ts: uint256) -> PriceParams:
    """
    @notice Obtain Price parameters true or assumed to be true at `parameters_ts`.
        Assumes constant locked_shares(to distribute) through distribution periods.
    @param parameters_ts Timestamp to obtain parameters for
    @return Assumed `PriceParams`
    """
    params: PriceParams = self.price_params
    if params.full_profit_unlock_date >= parameters_ts:
        return params

    period: uint256 = self.profit_max_unlock_time
    max_periods: uint256 = self.max_v2_duration
    number_of_periods: uint256 = min((parameters_ts - params.full_profit_unlock_date) // period + 1, max_periods)

    for i: uint256 in range(number_of_periods, bound=MAX_V2_DURATION):
        params.total_supply += params.balance_of_self
        params.total_idle += params.balance_of_self * (params.total_idle + params.total_debt) // params.total_supply

    params.total_supply += number_of_periods * params.balance_of_self
    params.full_profit_unlock_date += number_of_periods * period
    params.last_profit_update += number_of_periods * period
    return params
```
