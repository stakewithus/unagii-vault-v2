import brownie
import pytest


def test_harvest(strategy, daiVault, admin, treasury, dai, dai_whale):
    token = dai
    whale = dai_whale
    vault = daiVault

    # deposit into fund manager
    deposit_amount = 100 * 10 ** 18
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

    # create profit
    # min_profit = 10 ** 18
    min_profit = 0
    # token.transfer(strategy, min_profit, {"from": whale})

    before = snapshot()
    strategy.harvest(min_profit, {"from": admin})
    after = snapshot()

    print(before)
    print(after)

    assert after["strategy"]["totalAssets"] >= before["strategy"]["totalAssets"]
    assert after["token"]["strategy"] >= before["token"]["strategy"]
    assert after["token"]["treasury"] >= before["token"]["treasury"]
