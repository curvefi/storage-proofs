# pragma version ~=0.4

from contracts.blockhash import IBlockHashOracle

implements: IBlockHashOracle

block_hash: public(HashMap[uint256, bytes32])
state_root: public(HashMap[uint256, bytes32])

fallback_hash: bytes32


@view
@external
def get_block_hash(_number: uint256) -> bytes32:
    if self.block_hash[_number] == empty(bytes32):
        return self.fallback_hash
    else:
        return self.block_hash[_number]


@external
def _set_block_hash(_block_n: uint256, _block_hash: bytes32):
    self.block_hash[_block_n] = _block_hash


@view
@external
def get_state_root(_number: uint256) -> bytes32:
    if self.state_root[_number] == empty(bytes32):
        return self.fallback_hash
    else:
        return self.state_root[_number]


@external
def _set_state_root(_block_n: uint256, _state_root: bytes32):
    self.state_root[_block_n] = _state_root


@view
@external
def find_known_block_number(_before: uint256 = 0) -> uint256:
    raise "NotImplemented"
