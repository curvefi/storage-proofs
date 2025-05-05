import boa
import pytest


@pytest.fixture(scope="module")
def voracle(admin):
    with boa.env.prank(admin):
        return boa.load("contracts/vecrv/VecrvOracle.vy")


@pytest.fixture(scope="module", autouse=True)
def set_verifiers(voracle, admin, delegation_verifier, vecrv_verifier):
    with boa.env.prank(admin):
        voracle.grantRole(voracle.DELEGATION_VERIFIER(), delegation_verifier)
        voracle.grantRole(voracle.BALANCE_VERIFIER(), vecrv_verifier)
        voracle.grantRole(voracle.TOTAL_VERIFIER(), vecrv_verifier)
