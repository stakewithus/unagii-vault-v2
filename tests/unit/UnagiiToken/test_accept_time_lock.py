import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_accept_time_lock(uToken, user):
    timeLock = uToken.timeLock()
    uToken.setNextTimeLock(user, {"from": timeLock})

    # not next time lock
    with brownie.reverts("!next time lock"):
        uToken.acceptTimeLock({"from": timeLock})

    tx = uToken.acceptTimeLock({"from": user})
    assert uToken.timeLock() == user
    assert uToken.nextTimeLock() == ZERO_ADDRESS
    assert tx.events["AcceptTimeLock"].values() == [user]