import boa

import pytest

boa.env.enable_fast_mode()

EMPTY_BYTES32 = "0x0000000000000000000000000000000000000000000000000000000000000000"

pytest_plugins = [
    "shared.forked.fixtures",
]


def pytest_addoption(parser):
    parser.addoption(
        "--forked", action="store_true", default=False, help="Run tests in forked environment"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--forked"):
        return

    # Skip tests in `forked/` directory unless --forked is provided
    skip_forked = pytest.mark.skip(reason="Need --forked option to run")
    for item in items:
        if item.path and "/forked/" in str(item.path):
            item.add_marker(skip_forked)


@pytest.fixture(scope="session")
def anne():
    """
    "How wonderful it is that nobody need wait a single moment before starting to improve the world."
    – Anne Frank
    """
    return boa.env.generate_address()


@pytest.fixture(scope="session")
def leo():
    """
    "Everyone thinks of changing the world, but no one thinks of changing himself."
    – Leo Tolstoy
    """
    return boa.env.generate_address()


@pytest.fixture(scope="session")
def admin():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def boracle():
    return boa.load("tests/mocks/BlockhashOracleMock.vy", 21369420)
