import brownie
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_constructor(strategyEthTest, testEthFundManager, admin, treasury):
    fundManager = testEthFundManager

    assert strategyEthTest.timeLock() == admin
    assert strategyEthTest.admin() == admin
    assert strategyEthTest.treasury() == treasury

    assert strategyEthTest.fundManager() == fundManager
    assert strategyEthTest.token() == ETH
