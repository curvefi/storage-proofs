# pragma version ~=0.4

from contracts.scrvusd.oracles import ScrvusdOracleV2


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

price_params: PriceParams
price_params_ts: uint256
last_block_number: public(uint256)

profit_max_unlock_time: public(uint256)


@external
def update_price(_parameters: uint256[ScrvusdOracleV2.ALL_PARAM_CNT], _ts: uint256, _block_number: uint256) -> uint256:
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
    self.last_block_number = _block_number
    return 10 ** 18


@external
def update_profit_max_unlock_time(_profit_max_unlock_time: uint256, _block_number: uint256) -> bool:
    self.profit_max_unlock_time = _profit_max_unlock_time
    self.last_block_number = _block_number
    return True
