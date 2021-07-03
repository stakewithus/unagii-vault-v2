import brownie
import pytest


def test_deposit(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    amount = 10 ** 18
    eth_whale.transfer(fundManager, amount)

    def snapshot():
        return {
            "eth": {
                "fundManager": fundManager.balance(),
                "strategy": strategy.balance(),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    before = snapshot()
    tx = strategy.deposit(2 ** 256 - 1, 1, {"from": admin})
    after = snapshot()

    # # print(before)
    # # print(after)
    # # for e in tx.events:
    # #     print(e)

    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] - amount
    # all ETH were deposited into Convex
    assert after["eth"]["strategy"] == before["eth"]["strategy"]
    assert (
        after["strategy"]["totalAssets"] - before["eth"]["strategy"] >= 0.999 * amount
    )
