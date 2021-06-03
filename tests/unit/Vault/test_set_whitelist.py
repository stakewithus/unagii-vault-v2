import brownie
import pytest


def test_set_whitelist(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setWhitelist(user, True, {"from": user})

    # admin can call
    tx = vault.setWhitelist(user, True, {"from": admin})
    assert vault.whitelist(user)
    assert len(tx.events) == 1
    assert tx.events["SetWhitelist"].values() == [user, True]
