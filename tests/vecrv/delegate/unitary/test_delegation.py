import boa


def test_delegation(delegate, anne, leo):
    chain_id = 12

    assert delegate.delegator(chain_id, anne) == anne
    assert delegate.delegated(chain_id, leo) == leo
    assert not delegate.delegation_allowed(chain_id, leo)

    with boa.reverts():  # Not allowed
        with boa.env.prank(anne):
            delegate.delegate(chain_id, leo)

    with boa.env.prank(leo):
        delegate.allow_delegation(chain_id)

    assert delegate.delegator(chain_id, anne) == anne
    assert delegate.delegated(chain_id, leo) == leo
    assert delegate.delegation_allowed(chain_id, leo)

    with boa.env.prank(anne):
        delegate.delegate(chain_id, leo)

    assert delegate.delegated(chain_id, anne) == leo
    assert delegate.delegator(chain_id, leo) == anne
    assert not delegate.delegation_allowed(chain_id, leo)

    with boa.reverts():  # Not allowed
        with boa.env.prank(boa.env.generate_address()):
            delegate.delegate(chain_id, leo)


def test_remove_delegation(delegate, anne, leo):
    chain_id = 123
    with boa.env.prank(leo):
        delegate.allow_delegation(chain_id)
    with boa.env.prank(anne):
        delegate.delegate(chain_id, leo)

    # Remove by anne
    with boa.env.anchor():
        with boa.env.prank(anne):
            delegate.allow_delegation(chain_id)
            delegate.delegate(chain_id, anne)
        assert delegate.delegator(chain_id, anne) == anne
        assert delegate.delegated(chain_id, leo) == leo
        assert not delegate.delegation_allowed(chain_id, leo)

    # Remove by leo
    with boa.env.anchor():
        with boa.env.prank(leo):
            delegate.allow_delegation(chain_id, False)
        assert delegate.delegator(chain_id, anne) == anne
        assert delegate.delegated(chain_id, leo) == leo
        assert not delegate.delegation_allowed(chain_id, leo)


def test_delegation_by_dao(delegate, anne, leo):
    owner = delegate.owner()
    chain_id = 1234

    assert delegate.delegator(chain_id, anne) == anne
    assert delegate.delegated(chain_id, leo) == leo
    assert not delegate.delegation_allowed(chain_id, leo)

    with boa.reverts():  # arbitrary caller
        with boa.env.prank(boa.env.generate_address()):
            delegate.delegate_from(chain_id, anne, leo)
    with boa.reverts():  # call from anne
        with boa.env.prank(anne):
            delegate.delegate_from(chain_id, anne, leo)
    with boa.reverts():  # call from leo
        with boa.env.prank(leo):
            delegate.delegate_from(chain_id, anne, leo)

    with boa.env.prank(owner):
        delegate.delegate_from(chain_id, anne, leo)

    assert delegate.delegated(chain_id, anne) == leo
    assert delegate.delegator(chain_id, leo) == anne
    assert not delegate.delegation_allowed(chain_id, leo)
