import brownie
import pytest


DECIMALS = 18


def test_deposit(strategy, daiVault, admin, dai, dai_whale):
    token = dai
    whale = dai_whale
    vault = daiVault

    amount = 10 ** DECIMALS
    token.transfer(vault, amount, {"from": whale})

    calc = vault.calcMaxBorrow(strategy)
    assert calc > 0

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "strategy": token.balanceOf(strategy),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    before = snapshot()
    strategy.deposit(2 ** 256 - 1, calc, {"from": admin})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"] - calc
    # all token were deposited
    assert after["token"]["strategy"] == before["token"]["strategy"]
    assert (
        after["strategy"]["totalAssets"] - before["token"]["strategy"] >= 0.999 * calc
    )
