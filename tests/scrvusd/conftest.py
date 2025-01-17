import pytest
import boa

import eth_abi
import web3


@pytest.fixture(scope="module")
def crvusd():
    return boa.load("contracts/testing/MockERC20.vy", "CRV USD", "crvUSD", 18)


@pytest.fixture(scope="module")
def scrvusd(crvusd, admin):
    with boa.env.prank(admin):
        scrvusd = boa.load("contracts/testing/Vault.vy")
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


@pytest.fixture(scope="module", params=[10 ** 12])
def max_acceleration(request):
    return request.param


@pytest.fixture(scope="module")
def soracle(max_acceleration, admin):
    with boa.env.prank(admin):
        contract = boa.load("contracts/scrvusd/oracles/ScrvusdOracleV1.vy", 10 ** 18, max_acceleration)
    return contract


@pytest.fixture(scope="module")
def soracle_slots(scrvusd):
    return [
        21,  # total_debt
        22,  # total_idle, slot doesn't exist
        20,  # totalSupply
        38,  # full_profit_unlock_date
        39,  # profit_unlocking_rate
        40,  # last_profit_update
        int(web3.Web3.keccak(eth_abi.encode(["(uint256,address)"], [[18, scrvusd.address]])).hex(), 16),  # balance_of_self
    ]


@pytest.fixture(scope="module")
def verifier(soracle, admin):
    verifier = boa.env.generate_address()
    with boa.env.prank(admin):
        soracle.set_verifier(verifier)
    return verifier
