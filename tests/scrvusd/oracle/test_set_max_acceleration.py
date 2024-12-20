# import boa


# def test_default_behavior(scrvusd_rate_oracle, dev_deployer):
#     """
#     Test that the `set_max_acceleration` function correctly sets the value when called by the owner.
#     """
#     new_max_acceleration = 10**9  # A value within the valid range

#     # Call `set_max_acceleration` as the owner
#     scrvusd_rate_oracle.set_max_acceleration(new_max_acceleration, sender=dev_deployer)

#     # Verify the `max_acceleration` variable was updated correctly
#     assert scrvusd_rate_oracle.max_acceleration() == new_max_acceleration


# def test_access_control(scrvusd_rate_oracle):
#     """
#     Test that only the owner can call `set_max_acceleration`.
#     """
#     non_owner = boa.env.generate_address()
#     new_max_acceleration = 10**9

#     # Attempt to call `set_max_acceleration` as a non-owner
#     with boa.reverts("ownable: caller is not the owner"):
#         scrvusd_rate_oracle.set_max_acceleration(new_max_acceleration, sender=non_owner)


# def test_invalid_range(scrvusd_rate_oracle, dev_deployer):
#     """
#     Test that `set_max_acceleration` reverts when the value is out of the valid range.
#     """
#     too_low = 10**7  # Below the valid range
#     too_high = 10**19  # Above the valid range

#     # Test lower boundary
#     with boa.reverts():
#         scrvusd_rate_oracle.set_max_acceleration(too_low, sender=dev_deployer)

#     # Test upper boundary
#     with boa.reverts():
#         scrvusd_rate_oracle.set_max_acceleration(too_high, sender=dev_deployer)
