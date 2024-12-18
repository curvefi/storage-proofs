import boa


def test_default_behavior(oracle, dev_deployer):
    """
    Test that the `set_verifier` function correctly sets the verifier when called by the owner.
    """
    new_verifier = boa.env.generate_address()

    # Call `set_verifier` as the owner
    oracle.set_verifier(new_verifier, sender=dev_deployer)

    # Verify the event was emitted
    events = oracle.get_logs()
    assert f"SetVerifier(verifier={new_verifier}" in repr(events)

    # Verify the `verifier` variable was updated correctly
    assert oracle.verifier() == new_verifier


def test_access_control(oracle):
    """
    Test that only the owner can call `set_verifier`.
    """
    non_owner = boa.env.generate_address()
    new_verifier = boa.env.generate_address()

    # Attempt to call `set_verifier` as a non-owner
    with boa.reverts("ownable: caller is not the owner"):
        oracle.set_verifier(new_verifier, sender=non_owner)
