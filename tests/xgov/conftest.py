import boa
import pytest

from tests.conftest import WEEK, DAY

CHAIN_ID = boa.env.evm.chain.chain_id
DEFAULT_TTL = [
    WEEK,
    WEEK,
    DAY,
]


@pytest.fixture(scope="module")
def admins():
    return [boa.env.generate_address() for _ in range(3)]


@pytest.fixture(scope="module")
def broadcaster(admin, admins):
    with boa.env.prank(admin):
        return boa.load(
            "tests/xgov/contracts/curve-xgov/contracts/xyz/XYZBroadcaster.vy",
            admins,
            override_address="0x7BA33456EC00812C6B6BB6C1C3dfF579c34CC2cc",
        )


@pytest.fixture(scope="module")
def verifier():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def relayer(admin):
    with boa.env.prank(admin):
        return boa.load("tests/xgov/contracts/RelayerMock.vy")
