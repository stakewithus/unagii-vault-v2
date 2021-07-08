import brownie
import pytest


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_set_fund_manager(ethVault, testEthFundManager, admin, user):
    timeLock = ethVault.timeLock()
    fundManager = testEthFundManager

    with brownie.reverts("!time lock"):
        ethVault.setFundManager(user, {"from": user})

    # use user's address
    fundManager.setVault(user, {"from": admin})
    with brownie.reverts("fund manager vault != self"):
        ethVault.setFundManager(fundManager, {"from": timeLock})
    fundManager.setVault(ethVault, {"from": admin})

    # use user's address
    fundManager.setToken(user, {"from": admin})
    with brownie.reverts("fund manager token != ETH"):
        ethVault.setFundManager(fundManager, {"from": timeLock})
    fundManager.setToken(ETH, {"from": admin})

    tx = ethVault.setFundManager(fundManager, {"from": timeLock})
    assert ethVault.fundManager() == fundManager.address
    assert tx.events["SetFundManager"].values() == [fundManager.address]
