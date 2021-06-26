import brownie
import pytest


def test_constructor(strategyTest, testFundManager, token, admin, treasury):
    fundManager = testFundManager

    assert strategyTest.timeLock() == admin
    assert strategyTest.admin() == admin
    assert strategyTest.treasury() == treasury

    assert strategyTest.fundManager() == fundManager
    assert strategyTest.token() == token

    assert token.allowance(strategyTest, fundManager) == 2 ** 256 - 1
