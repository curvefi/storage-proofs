import boa


def test_delegation(delegate, alice, bob, empty_address):
    chain_id = 12

    assert delegate.delegation_target(chain_id, alice) == alice
    assert delegate.delegation_source(chain_id, bob) == bob
    assert not delegate.delegation_allowed(chain_id, bob)

    with boa.reverts():  # Not allowed
        with boa.env.prank(alice):
            delegate.delegate(chain_id, bob)

    with boa.env.prank(bob):
        delegate.allow_delegation(chain_id)

    assert delegate.delegation_target(chain_id, alice) == alice
    assert delegate.delegation_source(chain_id, bob) == bob
    assert delegate.delegation_allowed(chain_id, bob)

    with boa.env.prank(alice):
        delegate.delegate(chain_id, bob)

    assert delegate.delegation_target(chain_id, alice) == bob
    assert delegate.delegation_source(chain_id, bob) == alice
    assert not delegate.delegation_allowed(chain_id, bob)

    with boa.reverts():  # Not allowed
        with boa.env.prank(boa.env.generate_address()):
            delegate.delegate(chain_id, bob)


def test_remove_delegation(delegate, alice, bob, empty_address):
    chain_id = 123
    with boa.env.prank(bob):
        delegate.allow_delegation(chain_id)
    with boa.env.prank(alice):
        delegate.delegate(chain_id, bob)

    # Remove by alice
    with boa.env.anchor():
        with boa.env.prank(alice):
            delegate.allow_delegation(chain_id)
            delegate.delegate(chain_id, alice)
        assert delegate.delegation_target(chain_id, alice) == alice
        assert delegate.delegation_source(chain_id, bob) == bob
        assert not delegate.delegation_allowed(chain_id, bob)

    # Remove by bob
    with boa.env.anchor():
        with boa.env.prank(bob):
            delegate.allow_delegation(chain_id, False)
        assert delegate.delegation_target(chain_id, alice) == alice
        assert delegate.delegation_source(chain_id, bob) == bob
        assert not delegate.delegation_allowed(chain_id, bob)


def test_delegation_by_dao(delegate, alice, bob, empty_address):
    owner = delegate.owner()
    chain_id = 1234

    assert delegate.delegation_target(chain_id, alice) == alice
    assert delegate.delegation_source(chain_id, bob) == bob
    assert not delegate.delegation_allowed(chain_id, bob)

    with boa.reverts():  # arbitrary caller
        with boa.env.prank(boa.env.generate_address()):
            delegate.delegate_from(chain_id, alice, bob)
    with boa.reverts():  # call from alice
        with boa.env.prank(alice):
            delegate.delegate_from(chain_id, alice, bob)
    with boa.reverts():  # call from bob
        with boa.env.prank(bob):
            delegate.delegate_from(chain_id, alice, bob)

    with boa.env.prank(owner):
        delegate.delegate_from(chain_id, alice, bob)

    assert delegate.delegation_target(chain_id, alice) == bob
    assert delegate.delegation_source(chain_id, bob) == alice
    assert not delegate.delegation_allowed(chain_id, bob)
