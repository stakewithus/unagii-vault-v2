import brownie
import pytest


def test_set_next_time_lock(strategyTest, user):
    timeLock = strategyTest.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        strategyTest.setNextTimeLock(user, {"from": user})

    tx = strategyTest.setNextTimeLock(user, {"from": timeLock})
    assert strategyTest.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
