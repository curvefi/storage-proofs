import pytest


@pytest.fixture(scope="module")
def initial_price():
    return 11 * 10**17


def test_initial_price(soracle, initial_price):
    assert soracle.raw_price() == initial_price
    assert soracle.price_v0() == initial_price
    assert soracle.price_v1() == initial_price
    assert soracle.price_v2() == initial_price
