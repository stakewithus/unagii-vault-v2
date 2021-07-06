import brownie
from brownie import StrategyConvexAlUsdUsdt
import pytest


def test_migrate(strategy, usdtFundManager, admin, treasury, usdt, usdt_whale):
    token = usdt
    whale = usdt_whale

    fundManager = usdtFundManager

    # deposit into fund manager
    deposit_amount = 10 ** 6
    token.transfer(fundManager, deposit_amount, {"from": whale})

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, deposit_amount, {"from": admin})

    # new strategy
    timeLock = fundManager.timeLock()
    new_strategy = StrategyConvexAlUsdUsdt.deploy(
        fundManager, treasury, {"from": admin}
    )
    fundManager.approveStrategy(new_strategy, {"from": timeLock})
    new_strategy.authorize(strategy, True, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "new_strategy": token.balanceOf(new_strategy),
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

    assert after["token"]["strategy"] == 0
    assert after["strategy"]["totalAssets"] == 0
    assert after["token"]["new_strategy"] >= 0.99 * before["strategy"]["totalAssets"]
    assert after["new_strategy"]["totalAssets"] == after["token"]["new_strategy"]
