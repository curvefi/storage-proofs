# pragma version 0.4.0


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

# [address from][address to]
delegation_from: HashMap[address, address]
delegation_to: HashMap[address, address]
last_delegation: HashMap[address, uint256]

last_block_number: public(uint256)


@external
def update_balance(
    _user: address,
    _user_point_epoch: uint256,
    _user_point_history: Point,
    _locked: LockedBalance,
    _block_number: uint256,
):
    self.user_point_epoch[_user] = _user_point_epoch
    self.user_point_history[_user][_user_point_epoch] = _user_point_history
    self.locked[_user] = _locked

    self.last_block_number = _block_number


@external
def update_total(
    _epoch: uint256,
    _point_history: Point,
    _slope_changes: DynArray[int128, SLOPE_CHANGES_CNT],
    _block_number: uint256,
):
    self.epoch = _epoch
    self.point_history[_epoch] = _point_history

    start_time: uint256 = WEEK + (_point_history.ts // WEEK) * WEEK
    for i: uint256 in range(len(_slope_changes), bound=SLOPE_CHANGES_CNT):
        self.slope_changes[start_time + WEEK * i] = _slope_changes[i]

    self.last_block_number = _block_number


@external
def update_delegation(_from: address, _to: address, _block_number: uint256):
    self.delegation_from[_from] = _to
    self.delegation_to[_to] = _from

    self.last_block_number = _block_number
