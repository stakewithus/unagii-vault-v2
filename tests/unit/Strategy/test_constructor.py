def test_constructor(strategyTest, testVault, token, admin, treasury):
    vault = testVault
    strategy = strategyTest

    assert strategy.timeLock() == admin
    assert strategy.admin() == admin
    assert strategy.treasury() == treasury

    assert strategy.vault() == vault
    assert strategy.token() == token

    assert token.allowance(strategy, vault) == 2 ** 256 - 1

    assert strategy.minProfit() < strategy.maxProfit()
