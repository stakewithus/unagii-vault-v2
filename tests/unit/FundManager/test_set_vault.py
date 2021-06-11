import brownie
import pytest


def test_set_vault(fundManager, token, TestVault, testVault, user):
    vault = testVault
    timeLock = fundManager.timeLock()

    with brownie.reverts("!time lock"):
        fundManager.setVault(user, {"from": user})

    # use user's address
    vault.setToken(user, {"from": timeLock})
    with brownie.reverts("vault token != token"):
        fundManager.setVault(vault, {"from": timeLock})

    vault.setToken(token, {"from": timeLock})

    tx = fundManager.setVault(vault, {"from": timeLock})
    assert fundManager.vault() == vault
    assert token.allowance(fundManager, vault) == 2 ** 256 - 1
    assert tx.events["SetVault"].values() == [vault]

    # test approval is reset to 0 on old vault
    oldVault = vault
    newVault = TestVault.deploy(token, {"from": timeLock})

    fundManager.setVault(newVault, {"from": timeLock})

    assert token.allowance(fundManager, oldVault) == 0
    assert token.allowance(fundManager, newVault) == 2 ** 256 - 1
