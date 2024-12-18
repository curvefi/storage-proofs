import boa
import pytest

CURVE_DAO = boa.env.generate_address()


@pytest.fixture()
def curve_dao():
    return CURVE_DAO


@pytest.fixture()
def dev_deployer():
    return boa.env.generate_address()


@pytest.fixture()
def verifier_contract():
    return boa.env.generate_address()


@pytest.fixture()
def oracle_v1(dev_deployer, verifier_contract):
    oracle_deployer = boa.load_partial("contracts/scrvusd/oracles/ScrvusdOracleV1.vy")
    with boa.env.prank(dev_deployer):
        oracle = oracle_deployer(10**18, 10**10)
        oracle.set_prover(verifier_contract)
    return oracle
