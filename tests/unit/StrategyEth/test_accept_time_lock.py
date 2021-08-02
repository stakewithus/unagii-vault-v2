import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_accept_time_lock(strategyEthTest, user):
    timeLock = strategyEthTest.timeLock()

    strategyEthTest.setNextTimeLock(user, {"from": timeLock})

    # not next time lock
    with brownie.reverts("!next time lock"):
        strategyEthTest.acceptTimeLock({"from": timeLock})

    tx = strategyEthTest.acceptTimeLock({"from": user})
    assert strategyEthTest.timeLock() == user
    assert strategyEthTest.nextTimeLock() == ZERO_ADDRESS
    assert tx.events["AcceptTimeLock"].values() == [user]