# pragma version 0.4.0
"""
@title Sonic Block Hash oracle
@notice A contract that saves L1 state roots.
@license MIT
@author curve.fi
@custom:version 0.1.0
@custom:security security@curve.fi
"""

import IBlockHashOracle
implements: IBlockHashOracle

version: public(constant(String[8])) = "0.1.0"

interface IStateOracle:
    def lastBlockNum() -> uint256: view
    def lastState() -> bytes32: view
    def lastUpdateTime() -> uint256: view
    def chainId() -> uint256: view


STATE_ORACLE: public(immutable(IStateOracle))

MAX_LOOKUP: constant(uint256) = 7 * 86400  # A week

state_root: public(HashMap[uint256, bytes32])
commitments: public(HashMap[address, HashMap[uint256, bytes32]])

last_applied: uint256


@deploy
def __init__(_state_oracle: IStateOracle):
    STATE_ORACLE = _state_oracle
    assert staticcall STATE_ORACLE.chainId() == 1


@view
@external
def get_block_hash(_number: uint256) -> bytes32:
    """
    @notice Query the block hash of a block.
    @dev Reverts for unknown block numbers or if not supported.
    @param _number Number of the block to look for.
    """
    raise "NotImplemented"


@view
@external
def get_state_root(_number: uint256) -> bytes32:
    """
    @notice Query the state root hash of a block.
    @dev Reverts for unknown block numbers or if not supported.
    @param _number Number of the block to look for.
    """
    state_root: bytes32 = self.state_root[_number]
    if state_root == empty(bytes32) and _number == staticcall STATE_ORACLE.lastBlockNum():
        # try fetching current data
        state_root = staticcall STATE_ORACLE.lastState()
    assert state_root != empty(bytes32)

    return state_root


@view
@external
def find_known_block_number(_before: uint256=0) -> uint256:
    """
    @notice Find known block number, not optimized for on-chain use.
        No guarantee to be the last available block.
    @dev Reverts if not supported or couldn't find.
    @param _before Max block number to look for (can be used as init search point).
    """
    last_applied: uint256 = self.last_applied
    if _before == 0 or last_applied < _before:
        return last_applied

    for i: uint256 in range(MAX_LOOKUP):
        if self.state_root[_before - i] != empty(bytes32):
            return _before - i
    raise "NotFound"


@internal
def _update_state_root() -> (uint256, bytes32):
    number: uint256 = staticcall STATE_ORACLE.lastBlockNum()
    hash: bytes32 = staticcall STATE_ORACLE.lastState()
    self.state_root[number] = hash

    self.last_applied = max(self.last_applied, number)
    return number, hash


@external
def commit() -> uint256:
    """
    @notice Commit (and apply) a state root.
    @dev Same as `apply()` but saves committer
    """
    number: uint256 = 0
    hash: bytes32 = empty(bytes32)
    number, hash = self._update_state_root()

    self.commitments[msg.sender][number] = hash
    log IBlockHashOracle.CommitBlockHash(msg.sender, number, hash)
    log IBlockHashOracle.ApplyBlockHash(number, hash)
    return number


@external
def apply() -> uint256:
    """
    @notice Apply a state root.
    """
    number: uint256 = 0
    hash: bytes32 = empty(bytes32)
    number, hash = self._update_state_root()

    log IBlockHashOracle.ApplyBlockHash(number, hash)
    return number
