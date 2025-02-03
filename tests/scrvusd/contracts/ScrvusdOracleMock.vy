# pragma version ~=0.4

from contracts.scrvusd.oracles import ScrvusdOracleV2


parameters: public(uint256[ScrvusdOracleV2.ALL_PARAM_CNT])
ts: public(uint256)
block_number: public(uint256)


@external
def update_price(_parameters: uint256[ScrvusdOracleV2.ALL_PARAM_CNT], _ts: uint256, _block_number: uint256) -> uint256:
    self.parameters = _parameters
    self.ts = _ts
    self.block_number = _block_number
    return 10 ** 18
