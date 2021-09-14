import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_deactivate_strategy(ethVault, admin, testStrategyEth, user):
    vault = ethVault
    strategy = testStrategyEth
    timeLock = vault.timeLock()

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 123, {"from": admin})

    # revert if not authorized
    with brownie.reverts("!auth"):
        vault.deactivateStrategy(strategy, {"from": user})

    def snapshot():
        return {"totalDebtRatio": vault.totalDebtRatio()}

    before = snapshot()
    tx = vault.deactivateStrategy(strategy, {"from": admin})
    after = snapshot()

    strat = vault.strategies(strategy)

    assert not strat["active"]
    assert strat["debtRatio"] == 0

    assert after["totalDebtRatio"] == before["totalDebtRatio"] - 123
    assert vault.activeStrategies(0) == ZERO_ADDRESS

    assert tx.events["DeactivateStrategy"].values() == [strategy]

    # revert if not active
    with brownie.reverts("!active"):
        vault.deactivateStrategy(strategy, {"from": admin})