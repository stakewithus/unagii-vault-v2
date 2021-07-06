import brownie
from brownie import StrategyConvexStEth
import pytest


def test_migrate(strategy, ethFundManager, admin, treasury, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    # deposit into fund manager
    deposit_amount = 10 ** 18
    eth_whale.transfer(fundManager, deposit_amount)

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, amount, {"from": admin})

    # new strategy
    timeLock = fundManager.timeLock()
    new_strategy = StrategyConvexStEth.deploy(fundManager, treasury, {"from": admin})
    fundManager.approveStrategy(new_strategy, {"from": timeLock})
    new_strategy.authorize(strategy, True, {"from": admin})

    def snapshot():
        return {
            "eth": {
                "strategy": strategy.balance(),
                "new_strategy": new_strategy.balance(),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
            "new_strategy": {"totalAssets": new_strategy.totalAssets()},
        }

    before = snapshot()
    tx = strategy.migrate(new_strategy, {"from": fundManager})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    assert after["eth"]["strategy"] == 0
    assert after["strategy"]["totalAssets"] == 0
    assert after["eth"]["new_strategy"] >= 0.99 * before["strategy"]["totalAssets"]
    assert after["new_strategy"]["totalAssets"] == after["eth"]["new_strategy"]
