import brownie
from brownie import ZERO_ADDRESS
import pytest


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_set_fund_manager(strategyEthTest, TestEthFundManager, testVault, admin, user):
    timeLock = strategyEthTest.timeLock()
    fundManager = strategyEthTest.fundManager()
    newFundManager = TestEthFundManager.deploy(testVault, ETH, {"from": admin})

    # not time lock
    with brownie.reverts("!time lock"):
        strategyEthTest.setFundManager(newFundManager, {"from": user})

    # new fund manager token != token
    newFundManager.setToken(ZERO_ADDRESS)
    with brownie.reverts("new fund manager token != ETH"):
        strategyEthTest.setFundManager(newFundManager, {"from": timeLock})

    newFundManager.setToken(ETH)

    tx = strategyEthTest.setFundManager(newFundManager, {"from": timeLock})

    assert tx.events["SetFundManager"].values() == [newFundManager]
