import brownie
from brownie import StrategyConvexAlUsdDai
import pytest


def test_claim_rewards(strategy, daiFundManager, admin, treasury, dai, dai_whale):
    token = dai
    whale = dai_whale

    fundManager = daiFundManager

    amount = 10 ** 18
    token.transfer(fundManager, amount, {"from": whale})

    strategy.deposit(2 ** 256 - 1, 1, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    min_profit = 1

    before = snapshot()
    tx = strategy.claimRewards(min_profit, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    profit = event["profit"]

    assert profit >= min_profit
    assert after["token"]["strategy"] >= before["token"]["strategy"] + profit
    assert (
        after["strategy"]["totalAssets"] >= before["strategy"]["totalAssets"] + profit
    )
