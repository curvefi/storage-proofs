# pragma version 0.4.0
"""
@title L2 Voting Escrow Oracle
@notice Handles veCRV balance (mainly for boosting)
@license MIT
@author curve.fi
@custom:version 0.1.0
@custom:security security@curve.fi
"""

from snekmate.auth import access_control

initializes: access_control
exports: (
    access_control.supportsInterface,
    access_control.hasRole,
    access_control.DEFAULT_ADMIN_ROLE,
    access_control.grantRole,
    access_control.revokeRole,
)


event UpdateTotal:
    _epoch: uint256


event UpdateBalance:
    _user: address
    _user_point_epoch: uint256


event Delegate:
    _from: address
    _to: address


struct LockedBalance:
    amount: int128
    end: uint256


struct Point:
    bias: int128
    slope: int128
    ts: uint256
    blk: uint256


WEEK: constant(uint256) = 86400 * 7
SLOPE_CHANGES_CNT: constant(uint256) = 24  # 6 months

BALANCE_VERIFIER: public(constant(bytes32)) = keccak256("BALANCE_VERIFIER")
TOTAL_VERIFIER: public(constant(bytes32)) = keccak256("TOTAL_VERIFIER")
DELEGATION_VERIFIER: public(constant(bytes32)) = keccak256("DELEGATION_VERIFIER")

epoch: public(uint256)
point_history: public(HashMap[uint256, Point])

user_point_epoch: public(HashMap[address, uint256])
user_point_history: public(HashMap[address, HashMap[uint256, Point]])

locked: public(HashMap[address, LockedBalance])
slope_changes: public(HashMap[uint256, int128])

# [chain id][address from][address to]
delegation_from: HashMap[address, address]
delegation_to: HashMap[address, address]
last_delegation: HashMap[address, uint256]

name: public(constant(String[64])) = "Vote-escrowed CRV"
symbol: public(constant(String[32])) = "veCRV"
decimals: public(constant(uint256)) = 18

version: public(constant(String[8])) = "0.1.0"


@deploy
def __init__():
    access_control.__init__()
    access_control._set_role_admin(BALANCE_VERIFIER, access_control.DEFAULT_ADMIN_ROLE)
    access_control._set_role_admin(TOTAL_VERIFIER, access_control.DEFAULT_ADMIN_ROLE)
    access_control._set_role_admin(DELEGATION_VERIFIER, access_control.DEFAULT_ADMIN_ROLE)


### Getter methods


@view
def _balanceOf(user: address, timestamp: uint256) -> uint256:
    epoch: uint256 = self.user_point_epoch[user]
    if epoch == 0:
        return 0

    last_point: Point = self.user_point_history[user][epoch]
    last_point.bias -= last_point.slope * convert(timestamp - last_point.ts, int128)
    if last_point.bias < 0:
        return 0

    return convert(last_point.bias, uint256)


@external
@view
def delegation_target(_from: address) -> address:
    """
    @notice Get contract balance being delegated to
    @param _from Address of delegator
    @return Destination address of delegation
    """
    addr: address = self.delegation_from[_from]
    if addr == empty(address):
        addr = _from
    return addr


@external
@view
def delegation_source(_to: address) -> address:
    """
    @notice Get contract delegating balance to `_to`
    @param _to Address of delegated to
    @return Address of delegator
    """
    addr: address = self.delegation_to[_to]
    if addr == empty(address):
        addr = _to
    return addr


@view
@external
def balanceOf(_user: address, _timestamp: uint256 = block.timestamp) -> uint256:
    """
    @notice Get veCRV balance of user
    @param _user Address of the user
    @param _timestamp Timestamp for the balance check
    @return Balance of user
    """
    if not self.delegation_from[_user] in [empty(address), _user]:
        return 0
    user: address = self.delegation_to[_user]
    if user == empty(address):
        user = _user
    return self._balanceOf(user, _timestamp)


@view
@external
def totalSupply(_timestamp: uint256 = block.timestamp) -> uint256:
    """
    @notice Calculate total voting power
    @param _timestamp Timestamp at which to check totalSupply
    @return Total supply
    """
    last_point: Point = self.point_history[self.epoch]
    t_i: uint256 = (last_point.ts // WEEK) * WEEK
    for i: uint256 in range(256):
        t_i += WEEK

        d_slope: int128 = 0
        if t_i > _timestamp:
            t_i = _timestamp
        else:
            d_slope = self.slope_changes[t_i]
            if d_slope == 0:
                break
        last_point.bias -= last_point.slope * convert(t_i - last_point.ts, int128)
        if t_i == _timestamp:
            break

        last_point.slope += d_slope
        last_point.ts = t_i

    if last_point.bias < 0:
        return 0

    return convert(last_point.bias, uint256)


@external
@view
def get_last_user_slope(addr: address) -> int128:
    """
    @notice Get the most recently recorded rate of voting power decrease for `addr`
    @param addr Address of the user wallet
    @return Value of the slope
    """
    uepoch: uint256 = self.user_point_epoch[addr]
    return self.user_point_history[addr][uepoch].slope


@external
@view
def locked__end(_addr: address) -> uint256:
    """
    @notice Get timestamp when `_addr`'s lock finishes
    @param _addr User wallet
    @return Epoch time of the lock end
    """
    return self.locked[_addr].end


### Verifiers' update methods


@external
def update_balance(
    _user: address,
    _user_point_epoch: uint256,
    _user_point_history: Point,
    _locked: LockedBalance,
):
    """
    @notice Update user balance
    @param _user Address of the user to verify for
    @param _user_point_epoch Last `_user`s checkpointed epoch
    @param _user_point_history Last `_user`s point history
    @param _locked `_user`s locked balance
    """
    access_control._check_role(BALANCE_VERIFIER, msg.sender)
    assert (
        self.user_point_epoch[_user] <= _user_point_epoch
        and self.user_point_history[_user][_user_point_epoch].ts <= _user_point_history.ts
    ), "Outdated update"

    self.user_point_epoch[_user] = _user_point_epoch
    self.user_point_history[_user][_user_point_epoch] = _user_point_history

    self.locked[_user] = _locked

    log UpdateBalance(_user, _user_point_epoch)


@external
def update_total(
    _epoch: uint256, _point_history: Point, _slope_changes: DynArray[int128, SLOPE_CHANGES_CNT]
):
    """
    @notice Update VotingEscrow global values
    @param _epoch Current epoch in VotingEscrow contract
    @param _point_history Last epoch point history
    @param _slope_changes Slope changes for upcoming epochs
    """
    access_control._check_role(TOTAL_VERIFIER, msg.sender)
    assert (
        self.epoch <= _epoch and self.point_history[_epoch].ts <= _point_history.ts
    ), "Outdated update"

    self.epoch = _epoch
    self.point_history[_epoch] = _point_history

    start_time: uint256 = WEEK + (_point_history.ts // WEEK) * WEEK
    for i: uint256 in range(len(_slope_changes), bound=SLOPE_CHANGES_CNT):
        self.slope_changes[start_time + WEEK * i] = _slope_changes[i]

    log UpdateTotal(_epoch)


@external
def update_delegation(_from: address, _to: address, _block_number: uint256):
    """
    @notice Update veCRV balance delegation
    @dev Block number is used to linearize updates
    @param _from Address being delegated
    @param _to Address delegated to
    @param _block_number Block number at which delegation holds true
    """
    access_control._check_role(DELEGATION_VERIFIER, msg.sender)
    assert self.last_delegation[_from] <= _block_number, "Outdated update"

    self.delegation_from[_from] = _to
    self.delegation_to[_to] = _from
    self.last_delegation[_from] = _block_number

    log Delegate(_from, _to)
