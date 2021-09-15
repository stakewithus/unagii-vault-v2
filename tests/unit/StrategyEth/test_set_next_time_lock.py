import brownie


def test_set_next_time_lock(strategyEthTest, user):
    strategy = strategyEthTest
    timeLock = strategy.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        strategy.setNextTimeLock(user, {"from": user})

    tx = strategy.setNextTimeLock(user, {"from": timeLock})
    assert strategy.nextTimeLock() == user
    assert tx.events["SetNextTimeLock"].values() == [user]
