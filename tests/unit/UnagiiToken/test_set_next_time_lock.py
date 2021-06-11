import brownie
import pytest


def test_set_next_time_lock(uToken, user):
    timeLock = uToken.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        uToken.setNextTimeLock(user, {"from": user})

    tx = uToken.setNextTimeLock(user, {"from": timeLock})
    assert uToken.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
