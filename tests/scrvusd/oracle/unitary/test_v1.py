import pytest
import boa

from tests.scrvusd.conftest import DEFAULT_MAX_ACCELERATION


@pytest.fixture(scope="module")
def soracle(admin):
    with boa.env.prank(admin):
        contract = boa.load("contracts/scrvusd/oracles/ScrvusdOracleV1.vy", 10**18)
    return contract


def test_ownership(soracle, admin, anne):
    assert soracle.owner() == admin

    # Reachable for admin
    with boa.env.prank(admin):
        soracle.set_max_acceleration(DEFAULT_MAX_ACCELERATION + 1)
        soracle.set_verifier(admin)

    # Not reachable for third party
    with boa.env.prank(anne):
        with boa.reverts():
            soracle.set_max_acceleration(DEFAULT_MAX_ACCELERATION + 2)
        with boa.reverts():
            soracle.set_verifier(anne)

    # Transferable
    with boa.env.prank(admin):
        soracle.transfer_ownership(anne)
    assert soracle.owner() == anne

    # Reachable for new owner
    with boa.env.prank(anne):
        soracle.set_max_acceleration(DEFAULT_MAX_ACCELERATION + 2)
        soracle.set_verifier(anne)

    # Renounceable, making it immutable
    with boa.env.prank(anne):
        soracle.renounce_ownership()
        with boa.reverts():
            soracle.set_max_acceleration(DEFAULT_MAX_ACCELERATION + 1)
        with boa.reverts():
            soracle.set_verifier(admin)


def test_setters(soracle, admin, anne):
    with boa.env.prank(admin):
        soracle.set_max_acceleration(DEFAULT_MAX_ACCELERATION + 1)
        assert soracle.max_acceleration() == DEFAULT_MAX_ACCELERATION + 1

        soracle.set_verifier(anne)
        assert soracle.verifier() == anne


def test_update_price(soracle, verifier, anne):
    ts = boa.env.evm.patch.timestamp
    price_1_5_parameters = [3, 0, 2, ts + 7 * 86400, 0, 0, 0]
    price_0_5_parameters = [2, 0, 3, ts + 7 * 86400, 0, 0, 0]

    # Not available to a third party
    with boa.env.prank(anne):
        with boa.reverts():
            soracle.update_price(
                price_1_5_parameters,
                ts + 100,  # timestamp
                10,  # block number
            )

    with boa.env.prank(verifier):
        soracle.update_price(
            price_1_5_parameters,
            ts + 100,  # timestamp
            10,  # block number
        )
        assert soracle.last_block_number() == 10

        # Linearizability by block number
        with boa.reverts():
            soracle.update_price(
                price_1_5_parameters,
                ts + 101,  # timestamp
                8,  # block number
            )

        # "Breaking" resubmit at same block
        soracle.update_price(
            price_0_5_parameters,
            ts + 99,  # timestamp
            10,  # block number
        )
