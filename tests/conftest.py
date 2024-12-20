import boa
import pytest


@pytest.fixture(scope="session")
def alice():
    return boa.env.generate_address()


@pytest.fixture(scope="session")
def bob():
    return boa.env.generate_address()


@pytest.fixture(scope="session")
def empty_address():
    return "0x0000000000000000000000000000000000000000"
