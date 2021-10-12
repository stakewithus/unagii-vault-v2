import brownie
import pytest


def test_skim(strategy, usdtFundManager, admin, usdt, usdt_whale):
    token = usdt
    whale = usdt_whale

    fundManager = usdtFundManager

    amount = 10 ** 6
    token.transfer(fundManager, amount, {"from": whale})

    strategy.deposit(2 ** 256 - 1, amount, {"from": admin})

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
    profit = 10 ** 6
    token.transfer(strategy, profit, {"from": whale})

    before = snapshot()
    tx = strategy.skim({"from": admin})
    after = snapshot()

    print(before)
    print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    profit = event["profit"]

    # print(profit)

    assert profit > 0
    assert after["token"]["strategy"] >= profit
    # check slippage is small
    assert after["strategy"]["totalAssets"] >= 0.99 * before["strategy"]["totalAssets"]
