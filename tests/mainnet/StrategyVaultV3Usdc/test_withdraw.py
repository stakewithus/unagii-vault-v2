import brownie
from brownie import chain
import pytest


def test_withdraw(strategy, usdcFundManager, admin, usdc, usdc_whale):
    token = usdc
    whale = usdc_whale

    fundManager = usdcFundManager

    # deposit into fund manager
    deposit_amount = 10 ** 6
    token.transfer(fundManager, deposit_amount, {"from": whale})

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, deposit_amount, {"from": admin})
    chain.mine(5)

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
