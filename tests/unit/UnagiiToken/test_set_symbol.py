import brownie
import pytest


def test_set_symbol(accounts, uToken):
    admin = uToken.admin()

    # not admin
    with brownie.reverts("!admin"):
        uToken.setSymbol("TEST123", {"from": accounts[1]})

    uToken.setSymbol("TEST123", {"from": admin})
    assert uToken.symbol() == "TEST123"
