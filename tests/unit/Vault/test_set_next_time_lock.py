import brownie
import pytest


def test_set_next_time_lock(vault, user):
    timeLock = vault.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        vault.setNextTimeLock(user, {"from": user})

    tx = vault.setNextTimeLock(user, {"from": timeLock})
    assert vault.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
