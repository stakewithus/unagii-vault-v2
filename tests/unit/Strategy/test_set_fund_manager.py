import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_set_fund_manager(strategyTest, TestFundManager, testVault, token, admin, user):
    timeLock = strategyTest.timeLock()
    fundManager = strategyTest.fundManager()
    newFundManager = TestFundManager.deploy(testVault, token, {"from": admin})

    # not time lock
    with brownie.reverts("!time lock"):
        strategyTest.setFundManager(newFundManager, {"from": user})

    # new fund manager token != token
    newFundManager.setToken(ZERO_ADDRESS)
    with brownie.reverts("new fund manager token != token"):
        strategyTest.setFundManager(newFundManager, {"from": timeLock})

    newFundManager.setToken(token)

    tx = strategyTest.setFundManager(newFundManager, {"from": timeLock})

    assert tx.events["SetFundManager"].values() == [newFundManager]
    assert token.allowance(strategyTest, fundManager) == 0
    assert token.allowance(strategyTest, newFundManager) == 2 ** 256 - 1
