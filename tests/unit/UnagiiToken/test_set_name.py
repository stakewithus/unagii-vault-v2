import brownie
import pytest


def test_set_name(accounts, uToken):
    admin = uToken.admin()

    # not admin
    with brownie.reverts("!admin"):
        uToken.setName("test123", {"from": accounts[1]})

    uToken.setName("test123", {"from": admin})
    assert uToken.name() == "test123"
