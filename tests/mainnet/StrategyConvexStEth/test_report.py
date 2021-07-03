import brownie
import pytest


def test_report(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    amount = 10 ** 18
    eth_whale.transfer(fundManager, amount)
    strategy.deposit(2 ** 256 - 1, 1, {"from": admin})

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
    whale.transfer(strategy, min_profit)

    before = snapshot()
    tx = strategy.report(0, 2 ** 256 - 1, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
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
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] + gain
