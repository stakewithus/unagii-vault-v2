import brownie
import pytest


def test_constructor(strategyV2Test, testVault, token, admin, treasury):
    vault = testVault
    strategy = strategyV2Test

    assert strategy.timeLock() == admin
    assert strategy.admin() == admin
    assert strategy.treasury() == treasury

    assert strategy.vault() == vault
    assert strategy.token() == token

    assert token.allowance(strategy, vault) == 2 ** 256 - 1

    assert strategy.minTvl() < strategy.maxTvl()
