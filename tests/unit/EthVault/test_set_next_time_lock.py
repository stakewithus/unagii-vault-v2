import brownie
import pytest


def test_set_next_time_lock(ethVault, user):
    timeLock = ethVault.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        ethVault.setNextTimeLock(user, {"from": user})

    tx = ethVault.setNextTimeLock(user, {"from": timeLock})
    assert ethVault.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
