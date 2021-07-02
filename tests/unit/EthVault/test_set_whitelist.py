import brownie
import pytest


def test_set_whitelist(ethVault, admin, user):
    timeLock = ethVault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        ethVault.setWhitelist(user, True, {"from": user})

    # time lock
    tx = ethVault.setWhitelist(user, True, {"from": timeLock})
    assert ethVault.whitelist(user)
    assert len(tx.events) == 1
    assert tx.events["SetWhitelist"].values() == [user, True]

    # admin
    ethVault.setWhitelist(user, False, {"from": admin})
    assert not ethVault.whitelist(user)
