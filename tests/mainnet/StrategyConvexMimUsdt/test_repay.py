import brownie
import pytest


def test_repay(strategy, usdtFundManager, admin, usdt, usdt_whale):
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

    before = snapshot()
    tx = strategy.repay(2 ** 256 - 1, 1, {"from": admin})
    after = snapshot()

    print(before)
    print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    repaid = event["repaid"]

    assert after["strategy"]["totalAssets"] == 0

    diff = before["strategy"]["totalAssets"] - after["strategy"]["totalAssets"]
    assert diff > 0
    assert repaid >= 0.99 * diff
    assert after["token"]["strategy"] == 0
    assert after["token"]["fundManager"] == before["token"]["fundManager"] + repaid
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] - repaid
