import brownie
import pytest


def test_set_fund_manager(vault, token, testFundManager, admin, user):
    timeLock = vault.timeLock()

    with brownie.reverts("!time lock"):
        vault.setFundManager(user, {"from": user})

    # use user's address
    testFundManager.setToken(user, {"from": admin})
    with brownie.reverts("fund manager token != token"):
        vault.setFundManager(testFundManager, {"from": timeLock})
    testFundManager.setToken(token, {"from": admin})

    # use user's address
    testFundManager.setVault(user, {"from": admin})
    with brownie.reverts("fund manager vault != vault"):
        vault.setFundManager(testFundManager, {"from": timeLock})
    testFundManager.setVault(vault, {"from": admin})

    tx = vault.setFundManager(testFundManager, {"from": timeLock})
    assert vault.fundManager() == testFundManager.address
    assert tx.events["SetFundManager"].values() == [testFundManager.address]
