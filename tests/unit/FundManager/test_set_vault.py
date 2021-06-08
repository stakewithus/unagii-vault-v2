import brownie
import pytest


def test_set_vault(fundManager, token, testVault, admin, user):
    with brownie.reverts("!admin"):
        fundManager.setVault(user, {"from": user})

    # use user's address
    testVault.setToken(user, {"from": admin})
    with brownie.reverts("vault token != token"):
        fundManager.setVault(testVault, {"from": admin})

    testVault.setToken(token, {"from": admin})

    tx = fundManager.setVault(testVault, {"from": admin})
    assert fundManager.vault() == testVault
    assert token.allowance(fundManager, testVault) == 2 ** 256 - 1
    assert tx.events["SetVault"].values() == [testVault]
