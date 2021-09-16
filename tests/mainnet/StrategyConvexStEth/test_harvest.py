import brownie
import pytest


DECIMALS = 18


def test_harvest(strategy, ethVault, admin, treasury, eth_whale):
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
            "eth": {
                "strategy": strategy.balance(),
                "vault": vault.balance(),
                "treasury": treasury.balance(),
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
    assert after["eth"]["strategy"] >= before["eth"]["strategy"]
    assert after["eth"]["treasury"] >= before["eth"]["treasury"]
