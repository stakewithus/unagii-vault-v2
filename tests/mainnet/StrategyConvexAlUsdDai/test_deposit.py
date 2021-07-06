import brownie
import pytest


def test_deposit(strategy, daiFundManager, admin, dai, dai_whale):
    token = dai
    whale = dai_whale

    fundManager = daiFundManager

    amount = 10 ** 18
    token.transfer(fundManager, amount, {"from": whale})

    def snapshot():
        return {
            "token": {
                "fundManager": token.balanceOf(fundManager),
                "strategy": token.balanceOf(strategy),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    before = snapshot()
    tx = strategy.deposit(2 ** 256 - 1, 1, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount
    # all token were deposited into Convex
    assert after["token"]["strategy"] == before["token"]["strategy"]
    assert (
        after["strategy"]["totalAssets"] - before["token"]["strategy"] >= 0.999 * amount
    )
