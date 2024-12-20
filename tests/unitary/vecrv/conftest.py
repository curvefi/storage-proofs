import boa
import pytest


@pytest.fixture(scope="module")
def delegate():
    return boa.load("contracts/vecrv/VecrvDelegate.vy")
