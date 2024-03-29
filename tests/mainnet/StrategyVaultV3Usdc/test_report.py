import brownie
from brownie import chain
import pytest


def test_report(strategy, usdcFundManager, admin, usdc, usdc_whale):
    token = usdc
    whale = usdc_whale

    fundManager = usdcFundManager

    amount = 10 ** 6
    token.transfer(fundManager, amount, {"from": whale})

    strategy.deposit(2 ** 256 - 1, amount, {"from": admin})
    chain.mine(5)

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
    min_profit = 10 ** 6
    token.transfer(strategy, min_profit, {"from": whale})

    before = snapshot()
    tx = strategy.report(0, 2 ** 256 - 1, {"from": admin})
    after = snapshot()

    print(before)
    print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    gain = event["gain"]
    loss = event["loss"]
    free = event["free"]
    total = event["total"]
    debt = event["debt"]

    print(gain, loss, free, total, debt)

    assert gain >= 0.99 * min_profit
    assert loss == 0
    assert free >= min_profit
    assert after["strategy"]["totalAssets"] <= before["strategy"]["totalAssets"] + gain
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"]
    assert after["token"]["fundManager"] == before["token"]["fundManager"] + gain
