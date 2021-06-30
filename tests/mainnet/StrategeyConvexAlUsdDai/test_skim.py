import brownie
from brownie import StrategyConvexAlUsdDai
import pytest


def test_skim(daiFundManager, admin, treasury, dai, dai_whale):
    token = dai
    whale = dai_whale

    fundManager = daiFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyConvexAlUsdDai.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    amount = 10 ** 18
    token.transfer(fundManager, amount, {"from": whale})

    strategy.deposit(2 ** 256 - 1, 1, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "fundManager": token.balanceOf(fundManager),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
            "fundManager": {"debt": fundManager.getDebt(strategy)},
        }

    # create profit
    profit = 10 ** 18
    token.transfer(strategy, profit, {"from": whale})

    before = snapshot()
    tx = strategy.skim({"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    profit = event["profit"]

    # print(profit)

    assert profit > 0
    assert after["token"]["strategy"] >= profit
    # check slippage is small
    assert after["strategy"]["totalAssets"] >= 0.99 * before["strategy"]["totalAssets"]
