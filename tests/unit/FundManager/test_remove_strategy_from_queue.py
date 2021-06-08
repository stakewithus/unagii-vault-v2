import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_remove_strategy_from_queue(fundManager, admin, keeper, testStrategy, user):
    strategy = testStrategy

    fundManager.approveStrategy(strategy, {"from": admin})
    fundManager.addStrategyToQueue(strategy, 123, {"from": keeper})

    # revert if not authorized
    with brownie.reverts("!auth"):
        fundManager.removeStrategyFromQueue(strategy, {"from": user})

    def snapshot():
        return {"totalDebtRatio": fundManager.totalDebtRatio()}

    before = snapshot()
    tx = fundManager.removeStrategyFromQueue(strategy, {"from": keeper})
    after = snapshot()

    strat = fundManager.strategies(strategy)

    assert not strat["active"]
    assert strat["debtRatio"] == 0

    assert after["totalDebtRatio"] == before["totalDebtRatio"] - 123
    assert fundManager.queue(0) == ZERO_ADDRESS

    assert tx.events["RemoveStrategyFromQueue"].values() == [strategy]

    # revert if not active
    with brownie.reverts("!active"):
        fundManager.removeStrategyFromQueue(strategy, {"from": keeper})