import brownie
import pytest


def test_withdraw(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    # deposit into fund manager
    deposit_amount = 10 ** 18
    eth_whale.transfer(fundManager, deposit_amount)

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, 1, {"from": admin})

    def snapshot():
        return {
            "eth": {
                "strategy": strategy.balance(),
                "fundManager": fundManager.balance(),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    withdraw_amount = deposit_amount / 2

    before = snapshot()
    tx = strategy.withdraw(withdraw_amount, {"from": fundManager})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    withdrawn = event["withdrawn"]
    loss = event["loss"]

    assert withdrawn >= 0.99 * withdraw_amount
    assert loss <= 0.01 * withdraw_amount
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] + withdrawn
    assert after["strategy"]["totalAssets"] >= 0.99 * (
        before["strategy"]["totalAssets"] - withdraw_amount
    )
