import brownie
import pytest


def test_set_fund_manager(vault, token, testFundManager, admin, user):
    timeLock = vault.timeLock()
    fundManager = testFundManager

    with brownie.reverts("!time lock"):
        vault.setFundManager(user, {"from": user})

    # use user's address
    fundManager.setToken(user, {"from": admin})
    with brownie.reverts("fund manager token != token"):
        vault.setFundManager(fundManager, {"from": timeLock})
    fundManager.setToken(token, {"from": admin})

    # use user's address
    fundManager.setVault(user, {"from": admin})
    with brownie.reverts("fund manager vault != self"):
        vault.setFundManager(fundManager, {"from": timeLock})
    fundManager.setVault(vault, {"from": admin})

    tx = vault.setFundManager(fundManager, {"from": timeLock})
    assert vault.fundManager() == fundManager.address
    assert tx.events["SetFundManager"].values() == [fundManager.address]
