import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_remove_strategy_to_queue(vault, timeLock, keeper, strategy, user):
    vault.approveStrategy(strategy, 0, 0, 0, {"from": timeLock})
    vault.addStrategyToQueue(strategy, 1, {"from": keeper})

    # revert if not authorized
    with brownie.reverts("!auth"):
        vault.removeStrategyFromQueue(strategy, {"from": user})

    totalDebtRatio = vault.totalDebtRatio()
    tx = vault.removeStrategyFromQueue(strategy, {"from": keeper})
    strat = vault.strategies(strategy)

    assert not strat["active"]
    assert strat["debtRatio"] == 0

    assert vault.totalDebtRatio() == totalDebtRatio - 1
    assert vault.queue(0) == ZERO_ADDRESS

    # revert if not active
    with brownie.reverts("!active"):
        vault.removeStrategyFromQueue(strategy, {"from": keeper})