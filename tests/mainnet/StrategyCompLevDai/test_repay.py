import brownie
import pytest


def test_repay(strategy, daiVault, admin, dai, dai_whale):
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

    repaid = after["token"]["vault"] - before["token"]["vault"]
    assert repaid >= 0.99 * repay_amount
    # less than 0.01% slip
    assert (
        before["strategy"]["totalAssets"] - after["strategy"]["totalAssets"]
        <= 1.0001 * repay_amount
    )
    assert before["vault"]["debt"] - after["vault"]["debt"] == repaid
