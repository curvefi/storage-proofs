# pragma version ~=0.4

block_hash: public(HashMap[uint256, bytes32])
fallback_hash: public(bytes32)


@deploy
def __init__(_fallback_hash: bytes32):
    self.fallback_hash = _fallback_hash


@external
def get_block_hash(_number: uint256) -> bytes32:
    if self.block_hash[_number] == empty(bytes32):
        return self.fallback_hash
    else:
        return self.block_hash[_number]


@external
def set_block_hash(_block_n: uint256, _block_hash: bytes32):
    self.block_hash[_block_n] = _block_hash
