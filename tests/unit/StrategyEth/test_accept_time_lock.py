import brownie
from brownie import ZERO_ADDRESS


def test_accept_time_lock(strategyEthTest, user):
    strategy = strategyEthTest
    timeLock = strategy.timeLock()

    # not next time lock
    with brownie.reverts("!next time lock"):
        strategy.acceptTimeLock({"from": user})

    strategy.setNextTimeLock(user, {"from": timeLock})

    tx = strategy.acceptTimeLock({"from": user})
    assert strategy.timeLock() == user
    assert strategy.nextTimeLock() == ZERO_ADDRESS
    assert tx.events["AcceptTimeLock"].values() == [user]