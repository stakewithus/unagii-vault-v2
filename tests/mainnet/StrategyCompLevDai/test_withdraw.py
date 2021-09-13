import brownie
import pytest


def test_withdraw(strategy, daiVault, admin, dai, dai_whale):
    token = dai
    whale = dai_whale
    vault = daiVault

    # deposit into fund manager
    deposit_amount = 10 ** 18
    token.transfer(vault, deposit_amount, {"from": whale})

    calc = vault.calcMaxBorrow(strategy)
    assert calc > 0

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, calc, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "vault": token.balanceOf(vault),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    total = strategy.totalAssets()
    assert total >= calc * 0.99
    withdraw_amount = total / 2

    before = snapshot()
    strategy.withdraw(withdraw_amount, {"from": vault})
    after = snapshot()

    print(before)
    print(after)

    withdrawn = after["token"]["vault"] - before["token"]["vault"]
    assert withdrawn >= 0.99 * withdraw_amount
    # less than 0.01% slip
    assert (
        before["strategy"]["totalAssets"] - after["strategy"]["totalAssets"]
        <= 1.0001 * withdraw_amount
    )
