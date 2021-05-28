import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_approve_strategy(vault, token, admin, strategy, timeLock):
    # revert if paused
    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.approveStrategy(strategy, 0, 0, 0, {"from": timeLock})

    vault.setPause(False, {"from": admin})

    # revert if not time lock
    with brownie.reverts("!time lock"):
        vault.approveStrategy(strategy, 0, 0, 0, {"from": admin})

    # revert if strategy.vault != vault
    strategy.setVault(ZERO_ADDRESS)
    with brownie.reverts("!vault"):
        vault.approveStrategy(strategy, 0, 0, 0, {"from": timeLock})

    strategy.setVault(vault)

    # revert if strategy.token != token
    strategy.setToken(ZERO_ADDRESS)
    with brownie.reverts("!token"):
        vault.approveStrategy(strategy, 0, 0, 0, {"from": timeLock})

    strategy.setToken(token)

    # revert if minDebtPerHarvest > maxDebtPerHarvest
    with brownie.reverts("min > max"):
        vault.approveStrategy(strategy, 1, 0, 0, {"from": timeLock})

    # revert if perf fee > max
    with brownie.reverts("perf fee > max"):
        vault.approveStrategy(strategy, 0, 0, 5001, {"from": timeLock})

    vault.approveStrategy(strategy, 1, 2, 3, {"from": timeLock})
    strat = vault.strategies(strategy)

    assert strat["approved"]
    assert not strat["active"]
    assert strat["activatedAt"] == 0
    assert strat["debtRatio"] == 0
    assert strat["debt"] == 0
    assert strat["totalGain"] == 0
    assert strat["totalLoss"] == 0
    assert strat["minDebtPerHarvest"] == 1
    assert strat["maxDebtPerHarvest"] == 2
    assert strat["perfFee"] == 3

    # revert if approved
    with brownie.reverts("approved"):
        vault.approveStrategy(strategy, 0, 0, 0, {"from": timeLock})
