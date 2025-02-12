import boa

import pytest

boa.env.enable_fast_mode()

EMPTY_BYTES32 = "0x0000000000000000000000000000000000000000000000000000000000000000"
WEEK = 7 * 86400

pytest_plugins = [
    "shared.forked.fixtures",
]


def pytest_addoption(parser):
    parser.addoption(
        "--forked", action="store_true", default=False, help="Run tests in forked environment"
    )
    parser.addoption("--slow", action="store_true", default=False, help="Run tests marked as slow")


def pytest_collection_modifyitems(config, items):
    # Skip tests in `forked/` directories unless --forked is provided
    if not config.getoption("--forked"):
        skip_forked = pytest.mark.skip(reason="Skipping forked tests. Use --forked to enable them.")
        for item in items:
            if item.path and "/forked/" in str(item.path):
                item.add_marker(skip_forked)

    # Skip slow tests unless --slow is provided
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="Skipping slow tests. Use --slow to run them.")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    # Put integration tests after others
    items.sort(
        key=lambda item: [
            node if node != "integration" else "\uffff" for node in str(item.path).split("/")
        ]
    )


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
    return boa.load("tests/shared/contracts/BlockHashOracleMock.vy")
