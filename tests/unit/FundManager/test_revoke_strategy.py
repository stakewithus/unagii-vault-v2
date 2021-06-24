import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_revoke_strategy(fundManager, admin, testErc20Strategy, user):
    strategy = testErc20Strategy
    timeLock = fundManager.timeLock()

    # revert if not authorized
    with brownie.reverts("!auth"):
        fundManager.revokeStrategy(strategy, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        fundManager.revokeStrategy(strategy, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})

    # revert if active
    fundManager.addStrategyToQueue(strategy, 1, 0, 0, {"from": admin})

    with brownie.reverts("active"):
        fundManager.revokeStrategy(strategy, {"from": admin})

    fundManager.removeStrategyFromQueue(strategy, {"from": admin})

    tx = fundManager.revokeStrategy(strategy, {"from": admin})
    strat = fundManager.strategies(strategy)

    assert not strat["approved"]
    assert tx.events["RevokeStrategy"].values() == [strategy]
