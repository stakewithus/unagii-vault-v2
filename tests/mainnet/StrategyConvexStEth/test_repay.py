import brownie
import pytest


DECIMALS = 18


def test_repay(strategy, ethVault, admin, eth_whale):
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
            "vault": {"debt": vault.strategies(strategy)["debt"]},
        }

    total = strategy.totalAssets()
    assert total >= calc * 0.99
    repay_amount = total

    before = snapshot()
    strategy.repay(repay_amount, repay_amount * 0.99, {"from": admin})
    after = snapshot()

    print(before)
    print(after)

    repaid = after["eth"]["vault"] - before["eth"]["vault"]
    assert repaid >= 0.99 * repay_amount
    # less than 0.01% slip
    assert (
        before["strategy"]["totalAssets"] - after["strategy"]["totalAssets"]
        <= 1.0001 * repay_amount
    )
    assert before["vault"]["debt"] - after["vault"]["debt"] == repaid
