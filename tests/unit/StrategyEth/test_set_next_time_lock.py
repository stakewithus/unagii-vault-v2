import brownie
import pytest


def test_set_next_time_lock(strategyEthTest, user):
    timeLock = strategyEthTest.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        strategyEthTest.setNextTimeLock(user, {"from": user})

    tx = strategyEthTest.setNextTimeLock(user, {"from": timeLock})
    assert strategyEthTest.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
