# pragma version 0.4.0
"""
@title Taiko Block Hash oracle
@notice A contract that saves L1 state root hashes.
@license MIT
@author curve.fi
@custom:version 0.1.0
@custom:security security@curve.fi
"""

import IBlockHashOracle
implements: IBlockHashOracle

version: public(constant(String[8])) = "0.1.0"

interface ISignalService:
    def getSyncedChainData(_chainId: uint64, _kind: bytes32, _blockId: uint64) -> (uint64, bytes32): view

SIGNAL_SERVICE: constant(ISignalService) = ISignalService(0x1670000000000000000000000000000000000005)
H_STATE_ROOT: public(constant(bytes32)) = keccak256("STATE_ROOT")

MAX_LOOKUP: constant(uint256) = 3600 // 12  # An hour


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
    block_id: uint64 = empty(uint64)
    state_root: bytes32 = empty(bytes32)
    block_id, state_root = staticcall SIGNAL_SERVICE.getSyncedChainData(1, H_STATE_ROOT, convert(_number, uint64))
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
    assert _before > 0, "NeedMaxBlock"

    block_id: uint64 = empty(uint64)
    state_root: bytes32 = empty(bytes32)

    status: bool = False
    result: Bytes[64] = empty(Bytes[64])
    for i: uint256 in range(MAX_LOOKUP):
        status, result = raw_call(
            SIGNAL_SERVICE.address,
            abi_encode(
                convert(1, uint64),
                H_STATE_ROOT,
                convert(_before - i, uint64),
                method_id=method_id("getSyncedChainData(uint64,bytes32,uint64)"),
            ),
            max_outsize=64,
            is_static_call=True,
            revert_on_failure=False,
        )
        if not status:
            continue

        state_root = convert(slice(result, 32, 32), bytes32)
        if state_root != empty(bytes32):
            return _before - i
    raise "NotFound"
