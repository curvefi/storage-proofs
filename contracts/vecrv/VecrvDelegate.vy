# pragma version 0.4.0
"""
@title L2 veCRV delegation
@notice Handles veCRV delegation to use new addresses on other networks
@license MIT
@author curve.fi
@custom:version 0.0.1
@custom:security security@curve.fi
"""

from snekmate.auth import ownable

initializes: ownable
exports: (
    ownable.transfer_ownership,
    ownable.owner,
)


event AllowDelegation:
    _chain_id: indexed(uint256)
    _to: indexed(address)


event Delegate:
    _chain_id: indexed(uint256)
    _from: indexed(address)
    _to: address


# [chain id][address from][address to]
delegation_from: HashMap[uint256, HashMap[address, address]]
delegation_to: HashMap[uint256, HashMap[address, address]]

version: public(constant(String[8])) = "0.0.1"


@deploy
def __init__():
    ownable.__init__()


@external
@view
def delegated(_chain_id: uint256, _from: address) -> address:
    """
    @notice Get contract balance being delegated to
    @param _chain_id Chain ID to check for
    @param _from Address of delegator
    @return Destination address of delegation
    """
    addr: address = self.delegation_from[_chain_id][_from]
    if addr == empty(address):
        addr = _from
    return addr


@external
@view
def delegator(_chain_id: uint256, _to: address) -> address:
    """
    @notice Get contract delegating balance to `_to`
    @param _chain_id Chain ID to check for
    @param _to Address of delegated to
    @return Address of delegator
    """
    addr: address = self.delegation_to[_chain_id][_to]
    if addr in [empty(address), self]:
        return _to
    return addr


@external
@view
def delegation_allowed(_chain_id: uint256, _to: address) -> bool:
    """
    @notice Check whether delegation to this address is allowed
    @param _chain_id Chain ID to check for
    @param _to Address to check for
    @return True if allowed to delegate
    """
    return self.delegation_to[_chain_id][_to] == self


def _delegate(_chain_id: uint256, _from: address, _to: address):
    # Clean previous delegation
    prev_to: address = self.delegation_from[_chain_id][_from]
    if prev_to not in [empty(address), self]:
        self.delegation_to[_chain_id][prev_to] = empty(address)

    self.delegation_from[_chain_id][_from] = _to
    self.delegation_to[_chain_id][_to] = _from
    log Delegate(_chain_id, _from, _to)


@external
def delegate(_chain_id: uint256, _to: address):
    """
    @notice Delegate veCRV balance to another address
    @dev To revoke delegation set delegation to yourself
    @param _chain_id Chain ID where to set
    @param _to Address to delegate to
    """
    assert self.delegation_to[_chain_id][_to] == self, "Not allowed"
    self._delegate(_chain_id, msg.sender, _to)


@external
def allow_delegation(_chain_id: uint256, _allow: bool = True):
    """
    @notice Allow delegation to your address
    @dev Needed to deal with frontrun
    @param _chain_id Chaind ID to allow for
    @param _allow True(default) if allow, and False to remove delegation
    """
    # Clean current delegation
    _from: address = self.delegation_to[_chain_id][msg.sender]
    if _from not in [empty(address), self]:
        self.delegation_from[_chain_id][_from] = empty(address)
        log Delegate(_chain_id, _from, empty(address))

    if _allow:
        self.delegation_to[_chain_id][msg.sender] = self
        log AllowDelegation(_chain_id, msg.sender)
    else:
        self.delegation_to[_chain_id][msg.sender] = empty(address)


@external
def delegate_from(_chain_id: uint256, _from: address, _to: address):
    """
    @notice DAO-owned method to set delegation for non-reachable addresses
    @param _chain_id Chain ID where to set
    @param _from Address that delegates
    @param _to Address balance being delegated to
    """
    ownable._check_owner()

    self._delegate(_chain_id, _from, _to)
