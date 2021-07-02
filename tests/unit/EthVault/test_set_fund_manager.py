import brownie
import pytest


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_set_fund_manager(ethVault, testEthFundManager, admin, user):
    timeLock = ethVault.timeLock()

    with brownie.reverts("!time lock"):
        ethVault.setFundManager(user, {"from": user})

    # use user's address
    testEthFundManager.setVault(user, {"from": admin})
    with brownie.reverts("fund manager vault != self"):
        ethVault.setFundManager(testEthFundManager, {"from": timeLock})
    testEthFundManager.setVault(ethVault, {"from": admin})

    # use user's address
    testEthFundManager.setToken(user, {"from": admin})
    with brownie.reverts("fund manager token != token"):
        ethVault.setFundManager(testEthFundManager, {"from": timeLock})
    testEthFundManager.setToken(ETH, {"from": admin})

    tx = ethVault.setFundManager(testEthFundManager, {"from": timeLock})
    assert ethVault.fundManager() == testEthFundManager.address
    assert tx.events["SetFundManager"].values() == [testEthFundManager.address]
