# pragma version 0.3.10

from vyper.interfaces import ERC20
asset: public(address)
total_idle: uint256
profit_max_unlock_time: uint256
total_supply: uint256
balance_of: HashMap[address, uint256]
full_profit_unlock_date: uint256
profit_unlocking_rate: uint256
MAX_BPS_EXTENDED: constant(uint256) = 1_000_000_000_000
last_profit_update: uint256

enum Rounding:
    ROUND_DOWN
    ROUND_UP

@view
@internal
def _convert_to_shares(assets: uint256, rounding: Rounding) -> uint256:
    return 0

@view
@internal
def _unlocked_shares() -> uint256:
    return 0

@internal
def _issue_shares(shares: uint256, recipient: address):
    pass

@internal
def _burn_shares(shares: uint256, recipient: address):
    pass



@internal
def _process_report(strategy: address):
    # Cache `asset` for repeated use.
    _asset: address = self.asset

    total_assets: uint256 = 0
    current_debt: uint256 = 0

    # Accrue any airdropped `asset` into `total_idle`
    total_assets = ERC20(_asset).balanceOf(self)
    current_debt = self.total_idle

    gain: uint256 = 0


    ### Asses Gain or Loss ###

    # We have a gain.
    gain = unsafe_sub(total_assets, current_debt)

    ### Asses Fees and Refunds ###

    # Shares to lock is any amount that would otherwise increase the vaults PPS.
    shares_to_lock: uint256 = 0
    profit_max_unlock_time: uint256 = self.profit_max_unlock_time
    # Get the amount we will lock to avoid a PPS increase.
    if gain > 0 and profit_max_unlock_time != 0:
        shares_to_lock = self._convert_to_shares(gain, Rounding.ROUND_DOWN)

    # The total current supply including locked shares.
    total_supply: uint256 = self.total_supply
    # The total shares the vault currently owns. Both locked and unlocked.
    total_locked_shares: uint256 = self.balance_of[self]
    # Get the desired end amount of shares after all accounting.
    ending_supply: uint256 = total_supply + shares_to_lock - self._unlocked_shares()

    # If we will end with more shares than we have now.
    if ending_supply > total_supply:
        # Issue the difference.
        self._issue_shares(unsafe_sub(ending_supply, total_supply), self)

    # Else we need to burn shares.
    elif total_supply > ending_supply:
        # Can't burn more than the vault owns.
        to_burn: uint256 = min(unsafe_sub(total_supply, ending_supply), total_locked_shares)
        self._burn_shares(to_burn, self)

    # Record any reported gains.
    if gain > 0:
        # NOTE: this will increase total_assets
        current_debt = unsafe_add(current_debt, gain)
        self.total_idle = current_debt

    # Update unlocking rate and time to fully unlocked.
    total_locked_shares = self.balance_of[self]
    if total_locked_shares > 0:
        previously_locked_time: uint256 = 0
        _full_profit_unlock_date: uint256 = self.full_profit_unlock_date
        # Check if we need to account for shares still unlocking.
        if _full_profit_unlock_date > block.timestamp:
            # There will only be previously locked shares if time remains.
            # We calculate this here since it will not occur every time we lock shares.
            previously_locked_time = (total_locked_shares - shares_to_lock) * (_full_profit_unlock_date - block.timestamp)

        # new_profit_locking_period is a weighted average between the remaining time of the previously locked shares and the profit_max_unlock_time
        new_profit_locking_period: uint256 = (previously_locked_time + shares_to_lock * profit_max_unlock_time) / total_locked_shares
        # Calculate how many shares unlock per second.
        self.profit_unlocking_rate = total_locked_shares * MAX_BPS_EXTENDED / new_profit_locking_period
        # Calculate how long until the full amount of shares is unlocked.
        self.full_profit_unlock_date = block.timestamp + new_profit_locking_period
        # Update the last profitable report timestamp.
        self.last_profit_update = block.timestamp
    else:
        # NOTE: only setting this to the 0 will turn in the desired effect,
        # no need to update profit_unlocking_rate
        self.full_profit_unlock_date = 0