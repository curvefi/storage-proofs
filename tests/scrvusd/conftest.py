import pytest
import boa

import eth_abi
import eth_utils


DEFAULT_MAX_ACCELERATION = 2 * 10 ** 12
DEFAULT_MAX_V2_DURATION = 6 * 4


@pytest.fixture(scope="module")
def crvusd():
    return boa.load("tests/shared/contracts/ERC20Mock.vy", "CRV USD", "crvUSD", 18)


@pytest.fixture(scope="module")
def scrvusd(crvusd, admin):
    with boa.env.prank(admin):
        scrvusd = boa.load(
            "tests/scrvusd/contracts/Vault.vy",
            override_address="0x0655977feb2f289a4ab78af67bab0d17aab84367",
        )
        scrvusd.initialize(
            crvusd,
            "Savings crvUSD",
            "scrvUSD",
            admin,
            604800,  # profit_max_unlock_time
        )
        scrvusd.set_role(admin, 2 ** 14 - 1)
        scrvusd.set_deposit_limit(2 ** 256 - 1)
    return scrvusd


@pytest.fixture(scope="module")
def soracle(admin):
    with boa.env.prank(admin):
        contract = boa.load("tests/scrvusd/contracts/ScrvusdOracleMock.vy")
    return contract


@pytest.fixture(scope="module")
def soracle_price_slots(scrvusd):
    return [
        21,  # total_debt, slot doesn't exist
        22,  # total_idle
        20,  # total_supply
        38,  # full_profit_unlock_date
        39,  # profit_unlocking_rate
        40,  # last_profit_update
        int(eth_utils.keccak(eth_abi.encode(["(uint256,address)"], [[18, scrvusd.address]])).hex(), 16),  # balance_of_self
    ]


@pytest.fixture(scope="module")
def soracle_period_slots():
    return [37]


@pytest.fixture(scope="module")
def verifier():
    return boa.env.generate_address()
