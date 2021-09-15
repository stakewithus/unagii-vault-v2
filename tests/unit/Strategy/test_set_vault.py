import brownie
from brownie import ZERO_ADDRESS


def test_set_vault(strategyTest, TestVault, token, admin, user):
    strategy = strategyTest
    timeLock = strategy.timeLock()
    vault = strategy.vault()
    newVault = TestVault.deploy(token, {"from": admin})

    # not time lock
    with brownie.reverts("!time lock"):
        strategy.setVault(newVault, {"from": user})

    # new vault token != token
    newVault._setToken_(ZERO_ADDRESS)
    with brownie.reverts("new vault token != token"):
        strategy.setVault(newVault, {"from": timeLock})

    newVault._setToken_(token)

    tx = strategy.setVault(newVault, {"from": timeLock})

    assert tx.events["SetVault"].values() == [newVault]
    assert token.allowance(strategy, vault) == 0
    assert token.allowance(strategy, newVault) == 2 ** 256 - 1
