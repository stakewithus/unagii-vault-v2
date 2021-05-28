import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_add_strategy_to_queue(vault, admin, timeLock, keeper, strategy, user):
    # revert if paused
    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.addStrategyToQueue(strategy, 0, {"from": admin})

    vault.setPause(False, {"from": admin})

    # revert if not authorized
    with brownie.reverts("!auth"):
        vault.addStrategyToQueue(strategy, 0, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        vault.addStrategyToQueue(strategy, 0, {"from": admin})

    vault.approveStrategy(strategy, 0, 0, 0, {"from": timeLock})

    # revert if debt ratio > max
    with brownie.reverts("ratio > max"):
        vault.addStrategyToQueue(strategy, 100001, {"from": keeper})

    totalDebtRatio = vault.totalDebtRatio()
    tx = vault.addStrategyToQueue(strategy, 1, {"from": keeper})
    strat = vault.strategies(strategy)

    assert strat["active"]
    assert strat["activatedAt"] == tx.timestamp
    assert strat["debtRatio"] == 1

    assert vault.totalDebtRatio() == totalDebtRatio + 1
    assert vault.queue(0) == strategy

    # revert if active
    with brownie.reverts("active"):
        vault.addStrategyToQueue(strategy, 0, {"from": keeper})