import brownie
import pytest


def test_repay(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    amount = 10 ** 18
    eth_whale.transfer(fundManager, amount)

    strategy.deposit(2 ** 256 - 1, amount, {"from": admin})

    def snapshot():
        return {
            "eth": {
                "strategy": strategy.balance(),
                "fundManager": fundManager.balance(),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
            "fundManager": {"debt": fundManager.getDebt(strategy)},
        }

    before = snapshot()
    tx = strategy.repay(2 ** 256 - 1, 1, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    repaid = event["repaid"]

    assert after["strategy"]["totalAssets"] == 0

    diff = before["strategy"]["totalAssets"] - after["strategy"]["totalAssets"]
    assert diff > 0
    assert repaid >= 0.99 * diff
    assert after["eth"]["strategy"] == 0
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] + repaid
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] - repaid
