import brownie
from brownie import ZERO_ADDRESS


def test_add_strategy_to_queue(fundManager, admin, keeper, testStrategy, user):
    strategy = testStrategy

    # revert if not authorized
    with brownie.reverts("!auth"):
        fundManager.addStrategyToQueue(strategy, 0, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        fundManager.addStrategyToQueue(strategy, 0, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": admin})

    # revert if debt ratio > max
    with brownie.reverts("ratio > max"):
        fundManager.addStrategyToQueue(strategy, 100001, {"from": keeper})

    def snapshot():
        return {"totalDebtRatio": fundManager.totalDebtRatio()}

    before = snapshot()
    tx = fundManager.addStrategyToQueue(strategy, 123, {"from": keeper})
    after = snapshot()

    strat = fundManager.strategies(strategy)

    assert strat["active"]
    assert strat["activated"]
    assert strat["debtRatio"] == 123

    assert after["totalDebtRatio"] == before["totalDebtRatio"] + 123
    assert fundManager.queue(0) == strategy

    assert tx.events["AddStrategyToQueue"].values() == [strategy]

    # revert if active
    with brownie.reverts("active"):
        fundManager.addStrategyToQueue(strategy, 0, {"from": keeper})
