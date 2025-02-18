import boa
import pytest


@pytest.fixture(scope="module")
def voracle():
    return boa.load("contracts/vecrv/VecrvOracle.vy")
