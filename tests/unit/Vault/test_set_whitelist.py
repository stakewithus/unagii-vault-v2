import brownie
import pytest


def test_set_whitelist(vault, admin, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setWhitelist(user, True, {"from": user})

    # time lock
    tx = vault.setWhitelist(user, True, {"from": timeLock})
    assert vault.whitelist(user)
    assert len(tx.events) == 1
    assert tx.events["SetWhitelist"].values() == [user, True]

    # admin
    vault.setWhitelist(user, False, {"from": admin})
    assert not vault.whitelist(user)
