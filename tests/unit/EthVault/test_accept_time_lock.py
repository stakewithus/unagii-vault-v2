import brownie
import pytest


def test_accept_time_lock(ethVault, user):
    timeLock = ethVault.timeLock()

    ethVault.setNextTimeLock(user, {"from": timeLock})

    # not next time lock
    with brownie.reverts("!next time lock"):
        ethVault.acceptTimeLock({"from": timeLock})

    tx = ethVault.acceptTimeLock({"from": user})
    assert ethVault.timeLock() == user
    assert tx.events["AcceptTimeLock"].values() == [user]