import brownie
from brownie import ZERO_ADDRESS


def test_set_min_max_borrow(ethFundManager, admin, testStrategyEth, user):
    fundManager = ethFundManager
    strategy = testStrategyEth
    timeLock = fundManager.timeLock()

    # revert if not authorized
    with brownie.reverts("!auth"):
        fundManager.setMinMaxBorrow(strategy, 0, 0, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        fundManager.setMinMaxBorrow(strategy, 0, 0, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})

    # revert if min borrow > max borrow
    with brownie.reverts("min borrow > max borrow"):
        fundManager.setMinMaxBorrow(strategy, 2, 1, {"from": admin})

    tx = fundManager.setMinMaxBorrow(strategy, 11, 22, {"from": admin})

    strat = fundManager.strategies(strategy)

    assert strat["minBorrow"] == 11
    assert strat["maxBorrow"] == 22

    assert tx.events["SetMinMaxBorrow"].values() == [strategy, 11, 22]
