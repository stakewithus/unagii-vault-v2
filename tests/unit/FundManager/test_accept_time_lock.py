import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_accept_time_lock(fundManager, user):
    timeLock = fundManager.timeLock()

    fundManager.setNextTimeLock(user, {"from": timeLock})
    nextTimeLock = user

    # not next time lock
    with brownie.reverts("!next time lock"):
        fundManager.acceptTimeLock({"from": timeLock})

    tx = fundManager.acceptTimeLock({"from": nextTimeLock})
    assert fundManager.timeLock() == nextTimeLock
    assert fundManager.nextTimeLock() == ZERO_ADDRESS
    assert tx.events["AcceptTimeLock"].values() == [nextTimeLock]