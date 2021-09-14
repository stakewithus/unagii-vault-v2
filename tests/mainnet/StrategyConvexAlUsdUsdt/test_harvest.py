import brownie
import pytest


DECIMALS = 6


def test_harvest(strategy, usdtVault, admin, treasury, usdt, usdt_whale):
    token = usdt
    whale = usdt_whale
    vault = usdtVault

    # deposit into vault
    deposit_amount = 1000 * 10 ** DECIMALS
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
                "treasury": token.balanceOf(treasury),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    min_profit = 0

    before = snapshot()
    strategy.harvest(min_profit, {"from": admin})
    after = snapshot()

    print(before)
    print(after)

    assert after["strategy"]["totalAssets"] >= before["strategy"]["totalAssets"]
    assert after["token"]["strategy"] >= before["token"]["strategy"]
    assert after["token"]["treasury"] >= before["token"]["treasury"]
