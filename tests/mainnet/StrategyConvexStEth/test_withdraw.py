import brownie
import pytest


DECIMALS = 18


def test_withdraw(strategy, ethVault, admin, eth_whale):
    whale = eth_whale
    vault = ethVault

    # deposit into vault
    deposit_amount = 10 * 10 ** DECIMALS
    vault.setWhitelist(whale, True, {"from": admin})
    whale.transfer(vault, deposit_amount)

    calc = vault.calcMaxBorrow(strategy)
    assert calc > 0

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, calc, {"from": admin})

    def snapshot():
        return {
            "eth": {"strategy": strategy.balance(), "vault": vault.balance()},
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

    withdrawn = after["eth"]["vault"] - before["eth"]["vault"]
    assert withdrawn >= 0.99 * withdraw_amount
    # less than 0.01% slip
    assert (
        before["strategy"]["totalAssets"] - after["strategy"]["totalAssets"]
        <= 1.0001 * withdraw_amount
    )
