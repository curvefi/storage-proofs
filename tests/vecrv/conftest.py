import functools

import boa
import pytest

from scripts.vecrv.proof import get_delegation_slots


@pytest.fixture(scope="module")
def voracle():
    return boa.load("tests/vecrv/contracts/VecrvOracleMock.vy")


@pytest.fixture(scope="module")
def vecrv_balance_slots():
    def inner(addr):
        return []

    return inner


@pytest.fixture(scope="module")
def vecrv_total_slots():
    return []


@pytest.fixture(scope="module")
def delegate(admin):
    with boa.env.prank(admin):
        return boa.load(
            "contracts/vecrv/VecrvDelegate.vy",
            admin,
            override_address="0xde1e6A7E8297076f070E857130E593107A0E0cF5",
        )


@pytest.fixture(scope="module")
def delegate_slots():
    return functools.partial(get_delegation_slots, boa.env.evm.chain.chain_id)


@pytest.fixture(scope="module")
def delegation_verifier():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def vecrv_verifier():
    return boa.env.generate_address()
