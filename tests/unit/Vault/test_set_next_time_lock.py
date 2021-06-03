import brownie
import pytest


def test_set_next_time_lock(vault, timeLock, user):
    # not time lock
    with brownie.reverts("!time lock"):
        vault.setNextTimeLock(user, {"from": user})

    # new time lock is current time lock
    with brownie.reverts("next time lock = current"):
        vault.setNextTimeLock(timeLock, {"from": timeLock})

    tx = vault.setNextTimeLock(user, {"from": timeLock})
    assert vault.nextTimeLock() == user
    assert len(tx.events) == 1
    assert tx.events["SetNextTimeLock"].values() == [user]
