import brownie
import pytest


def test_accept_time_lock(strategyTest, user):
    timeLock = strategyTest.timeLock()

    strategyTest.setNextTimeLock(user, {"from": timeLock})

    # not next time lock
    with brownie.reverts("!next time lock"):
        strategyTest.acceptTimeLock({"from": timeLock})

    tx = strategyTest.acceptTimeLock({"from": user})
    assert strategyTest.timeLock() == user
    assert tx.events["AcceptTimeLock"].values() == [user]