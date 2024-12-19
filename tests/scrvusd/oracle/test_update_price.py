import boa
import time


def test_default_behavior(scrvusd_rate_oracle, verifier_mock):
    ts = int(time.time())
    params_array = [1, 0, 1, 0, 0, 0, 0]
    with boa.env.prank(verifier_mock):
        scrvusd_rate_oracle.update_price(params_array, ts)
        events = scrvusd_rate_oracle.get_logs()

    # Verify event emission
    assert f"PriceUpdate(new_price={10**18}, price_params_ts={ts}" in repr(events)

    assert scrvusd_rate_oracle.eval("self.price_params") == params_array
