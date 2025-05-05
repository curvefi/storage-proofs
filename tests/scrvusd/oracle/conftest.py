import boa
import pytest


@pytest.fixture(scope="module")
def initial_price():
    return 10**18


@pytest.fixture(scope="module")
def soracle(admin, initial_price):
    with boa.env.prank(admin):
        contract = boa.load("contracts/scrvusd/oracles/ScrvusdOracleV2.vy", initial_price)
    return contract


@pytest.fixture(scope="module", autouse=True)
def set_verifier(verifier, soracle, admin):
    with boa.env.prank(admin):
        if hasattr(soracle, "set_verifier"):
            soracle.set_verifier(verifier)
        else:
            soracle.grantRole(soracle.PRICE_PARAMETERS_VERIFIER(), verifier)
            soracle.grantRole(soracle.UNLOCK_TIME_VERIFIER(), verifier)
