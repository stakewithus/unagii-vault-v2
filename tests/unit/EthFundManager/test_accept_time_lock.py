import brownie
import pytest


def test_accept_time_lock(ethFundManager, user):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    fundManager.setNextTimeLock(user, {"from": timeLock})
    nextTimeLock = user

    # not next time lock
    with brownie.reverts("!next time lock"):
        fundManager.acceptTimeLock({"from": timeLock})

    tx = fundManager.acceptTimeLock({"from": nextTimeLock})
    assert fundManager.timeLock() == nextTimeLock
    assert tx.events["AcceptTimeLock"].values() == [nextTimeLock]