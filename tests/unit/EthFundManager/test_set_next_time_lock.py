import brownie
import pytest


def test_set_next_time_lock(ethFundManager, user):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        fundManager.setNextTimeLock(user, {"from": user})

    tx = fundManager.setNextTimeLock(user, {"from": timeLock})
    assert fundManager.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
