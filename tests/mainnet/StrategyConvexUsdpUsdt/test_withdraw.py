import brownie
import pytest


def test_withdraw(strategy, usdtFundManager, admin, usdt, usdt_whale):
    token = usdt
    whale = usdt_whale

    fundManager = usdtFundManager

    # deposit into fund manager
    deposit_amount = 10 ** 6
    token.transfer(fundManager, deposit_amount, {"from": whale})

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, deposit_amount, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "fundManager": token.balanceOf(fundManager),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    withdraw_amount = deposit_amount / 2

    before = snapshot()
    tx = strategy.withdraw(withdraw_amount, {"from": fundManager})
    after = snapshot()

    print(before)
    print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    withdrawn = event["withdrawn"]
    loss = event["loss"]

    assert withdrawn >= 0.99 * withdraw_amount
    assert loss <= 0.01 * withdraw_amount
    assert after["token"]["fundManager"] == before["token"]["fundManager"] + withdrawn
    assert after["strategy"]["totalAssets"] >= 0.99 * (
        before["strategy"]["totalAssets"] - withdraw_amount
    )
