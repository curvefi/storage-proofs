import pytest
import boa


@pytest.fixture(scope="module")
def initial_price():
    return 11 * 10**17


def test_initial_price(soracle, initial_price):
    for timedelta in [0, 60, 3600]:
        boa.env.time_travel(seconds=timedelta)
        assert soracle.raw_price() == initial_price
        assert soracle.price_v0() == initial_price
        assert soracle.price_v1() == initial_price
        assert soracle.price_v2() == initial_price
