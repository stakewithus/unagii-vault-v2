import brownie
from brownie import ZERO_ADDRESS


def test_set_vault(strategyV2Test, TestVault, token, admin, user):
    strategy = strategyV2Test
    timeLock = strategy.timeLock()
    vault = strategy.vault()
    newVault = TestVault.deploy(token, {"from": admin})

    # not time lock
    with brownie.reverts("!time lock"):
        strategy.setVault(newVault, {"from": user})

    # new vault token != token
    newVault.setToken(ZERO_ADDRESS)
    with brownie.reverts("new vault token != token"):
        strategy.setVault(newVault, {"from": timeLock})

    newVault.setToken(token)

    tx = strategy.setVault(newVault, {"from": timeLock})

    assert tx.events["SetVault"].values() == [newVault]
    assert token.allowance(strategy, vault) == 0
    assert token.allowance(strategy, newVault) == 2 ** 256 - 1
