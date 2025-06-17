import boa
import pytest

from tests.conftest import EMPTY_ADDRESS
from tests.xgov.conftest import CHAIN_ID


NONCES = [
    0,
    1,
    7,
]
MESSAGES = [
    [(EMPTY_ADDRESS, bytes.fromhex("00"))],
    [(EMPTY_ADDRESS, bytes.fromhex("01"))],
    [(EMPTY_ADDRESS, bytes.fromhex("02"))],
]


@pytest.fixture(scope="module", autouse=True)
def broadcast(broadcaster, admins):
    for i in range(3):
        with boa.env.prank(admins[i]):
            for _ in range(NONCES[i] + 1):
                broadcaster.broadcast(CHAIN_ID, MESSAGES[i])
