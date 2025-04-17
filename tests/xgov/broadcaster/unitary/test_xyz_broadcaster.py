import boa
import pytest

from tests.conftest import EMPTY_ADDRESS, DAY
from tests.xgov.conftest import CHAIN_ID, DEFAULT_TTL


def test_admins(broadcaster, admins, anne):
    returned_admins = broadcaster.admins()
    assert returned_admins.ownership == admins[0]
    assert returned_admins.parameter == admins[1]
    assert returned_admins.emergency == admins[2]

    new_admins = [boa.env.generate_address() for _ in range(3)]
    for addr in [admins[1], admins[2], anne]:
        with boa.env.prank(addr):
            with boa.reverts():  # only ownership
                broadcaster.commit_admins(new_admins)
    with boa.env.prank(admins[0]):
        broadcaster.commit_admins(new_admins)
        broadcaster.apply_admins()

    returned_admins = broadcaster.admins()
    assert returned_admins.ownership == new_admins[0]
    assert returned_admins.parameter == new_admins[1]
    assert returned_admins.emergency == new_admins[2]


@pytest.mark.parametrize("i", [0, 1, 2])
def test_broadcast(broadcaster, admins, i):
    assert broadcaster.nonce(2**i, CHAIN_ID) == 0
    with boa.env.prank(admins[i]):
        broadcaster.broadcast(CHAIN_ID, [(EMPTY_ADDRESS, bytes.fromhex(""))])
    assert broadcaster.nonce(2**i, CHAIN_ID) == 1


@pytest.mark.parametrize("i", [0, 1, 2])
def test_ttl(broadcaster, admins, i):
    with boa.env.prank(admins[i]):
        broadcaster.broadcast(CHAIN_ID, [(EMPTY_ADDRESS, bytes.fromhex(""))])
    assert broadcaster.deadline(2**i, CHAIN_ID, 0) == boa.env.timestamp + DEFAULT_TTL[i]

    with boa.env.prank(admins[i]):
        broadcaster.broadcast(CHAIN_ID, [(EMPTY_ADDRESS, bytes.fromhex(""))], DAY * 3 // 2)
    assert broadcaster.deadline(2**i, CHAIN_ID, 1) == boa.env.timestamp + DAY * 3 // 2

    with boa.env.prank(admins[i]):
        broadcaster.broadcast(CHAIN_ID, [(EMPTY_ADDRESS, bytes.fromhex(""))], 3 * DAY)
    assert broadcaster.deadline(2**i, CHAIN_ID, 2) == boa.env.timestamp + 3 * DAY
