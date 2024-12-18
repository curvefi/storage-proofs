import boa
import time


def test_update_price(curve_dao, oracle_v1, verifier_contract):
    ts = int(time.time())
    params_array = [1, 0, 1, 0, 0, 0, 0]
    with boa.env.prank(verifier_contract):
        oracle_v1.update_price(params_array, ts)
    assert oracle_v1.eval("self.price_params") == params_array
