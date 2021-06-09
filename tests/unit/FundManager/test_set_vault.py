import brownie
import pytest


def test_set_vault(fundManager, token, TestVault, testVault, admin, user):
    vault = testVault

    with brownie.reverts("!admin"):
        fundManager.setVault(user, {"from": user})

    # use user's address
    vault.setToken(user, {"from": admin})
    with brownie.reverts("vault token != token"):
        fundManager.setVault(vault, {"from": admin})

    vault.setToken(token, {"from": admin})

    tx = fundManager.setVault(vault, {"from": admin})
    assert fundManager.vault() == vault
    assert token.allowance(fundManager, vault) == 2 ** 256 - 1
    assert tx.events["SetVault"].values() == [vault]

    # test approval is reset to 0 on old vault
    oldVault = vault
    newVault = TestVault.deploy(token, {"from": admin})

    fundManager.setVault(newVault, {"from": admin})

    assert token.allowance(fundManager, oldVault) == 0
    assert token.allowance(fundManager, newVault) == 2 ** 256 - 1
