ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_constructor(strategyEthTest, testEthVault, admin, treasury):
    vault = testEthVault
    strategy = strategyEthTest

    assert strategy.timeLock() == admin
    assert strategy.admin() == admin
    assert strategy.treasury() == treasury

    assert strategy.vault() == vault
    assert strategy.token() == ETH

    assert strategy.minProfit() < strategy.maxProfit()
