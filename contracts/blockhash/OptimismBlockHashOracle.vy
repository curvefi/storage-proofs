# pragma version 0.4.0
"""
@title Optimism Block Hash oracle
@notice A contract that saves L1 block hashes.
@license MIT
@author curve.fi
@custom:version 0.0.1
@custom:security security@curve.fi
"""

version: public(constant(String[8])) = "0.0.1"

interface IL1Block:
    def number() -> uint64: view
    def hash() -> bytes32: view


event CommitBlockHash:
    committer: indexed(address)
    number: indexed(uint256)
    hash: bytes32

event ApplyBlockHash:
    number: indexed(uint256)
    hash: bytes32

L1_BLOCK: constant(IL1Block) = IL1Block(0x4200000000000000000000000000000000000015)

block_hash: public(HashMap[uint256, bytes32])
commitments: public(HashMap[address, HashMap[uint256, bytes32]])


@view
@external
def get_block_hash(_number: uint256) -> bytes32:
    """
    @notice Query the block hash of a block.
    @dev Reverts for block numbers which have yet to be set.
    """
    block_hash: bytes32 = self.block_hash[_number]
    assert block_hash != empty(bytes32)

    return block_hash


@view
@external
def get_state_root(_number: uint256) -> bytes32:
    """
    @notice Query the state root hash of a block.
    @dev Reverts for block numbers which have yet to be set.
    """
    raise "Not implemented"


@internal
def _update_block_hash() -> (uint256, bytes32):
    number: uint256 = convert(staticcall L1_BLOCK.number(), uint256)
    hash: bytes32 = staticcall L1_BLOCK.hash()
    self.block_hash[number] = hash

    return number, hash


@external
def commit() -> uint256:
    """
    @notice Commit (and apply) a block hash.
    @dev Same as `apply()` but saves committer
    """
    number: uint256 = 0
    hash: bytes32 = empty(bytes32)
    number, hash = self._update_block_hash()

    self.commitments[msg.sender][number] = hash
    log CommitBlockHash(msg.sender, number, hash)
    log ApplyBlockHash(number, hash)
    return number


@external
def apply() -> uint256:
    """
    @notice Apply a block hash.
    """
    number: uint256 = 0
    hash: bytes32 = empty(bytes32)
    number, hash = self._update_block_hash()

    log ApplyBlockHash(number, hash)
    return number
