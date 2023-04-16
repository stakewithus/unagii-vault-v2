import brownie
from brownie import chain
import pytest


def test_harvest(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    # deposit into fund manager
    deposit_amount = 10 ** 18
    eth_whale.transfer(fundManager, deposit_amount)

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, deposit_amount, {"from": admin})

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
    min_profit = 10 ** 18
    eth_whale.transfer(strategy, min_profit)

    before = snapshot()
    tx = strategy.harvest(1, 0, 2 ** 256 - 1, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    assert after["strategy"]["totalAssets"] >= before["fundManager"]["debt"]
    assert after["eth"]["fundManager"] >= before["eth"]["fundManager"]
