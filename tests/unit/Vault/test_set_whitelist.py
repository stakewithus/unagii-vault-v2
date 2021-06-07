import brownie
import pytest


def test_set_whitelist(vault, admin, keeper, user):
    # not auth
    with brownie.reverts("!auth"):
        vault.setWhitelist(user, True, {"from": user})

    # admin
    tx = vault.setWhitelist(user, True, {"from": admin})
    assert vault.whitelist(user)
    assert len(tx.events) == 1
    assert tx.events["SetWhitelist"].values() == [user, True]

    # keeper
    vault.setWhitelist(user, False, {"from": keeper})
    assert not vault.whitelist(user)
