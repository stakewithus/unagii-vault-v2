import brownie
import pytest

DECIMALS = 18


def test_deposit(strategy, ethVault, admin, eth_whale):
    whale = eth_whale
    vault = ethVault

    # send ETH to vault
    amount = 10 ** DECIMALS
    vault.setWhitelist(whale, True, {"from": admin})
    whale.transfer(vault, amount)

    calc = vault.calcMaxBorrow(strategy)
    assert calc > 0

    def snapshot():
        return {
            "eth": {
                "vault": vault.balance(),
                "strategy": strategy.balance(),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    before = snapshot()
    strategy.deposit(2 ** 256 - 1, calc, {"from": admin})
    after = snapshot()

    print(before)
    print(after)

    assert after["eth"]["vault"] == before["eth"]["vault"] - calc
    # all eth were deposited
    assert after["eth"]["strategy"] == before["eth"]["strategy"]
    assert after["strategy"]["totalAssets"] - before["eth"]["strategy"] >= 0.999 * calc
