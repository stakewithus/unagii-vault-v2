import brownie
from brownie import chain
import pytest


def test_skim(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    amount = 10 ** 18
    eth_whale.transfer(fundManager, amount)
    strategy.deposit(2 ** 256 - 1, amount, {"from": admin})

    # vault has blockDelay
    chain.mine(5);

    def snapshot():
        return {
            "eth": {
                "strategy": strategy.balance(),
                "fundManager": fundManager.balance(),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
            "fundManager": {"debt": fundManager.getDebt(strategy)},
        }

    # create profit
    profit = 10 ** 18
    whale.transfer(strategy, profit)

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
    assert after["eth"]["strategy"] >= profit
    # check slippage is small
    assert after["strategy"]["totalAssets"] >= 0.99 * before["strategy"]["totalAssets"]
