import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_revoke_strategy(fundManager, admin, keeper, guardian, testStrategy, user):
    strategy = testStrategy

    # revert if not authorized
    with brownie.reverts("!auth"):
        fundManager.revokeStrategy(strategy, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        fundManager.revokeStrategy(strategy, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": admin})

    # revert if active
    fundManager.addStrategyToQueue(strategy, 1, {"from": keeper})

    with brownie.reverts("active"):
        fundManager.revokeStrategy(strategy, {"from": keeper})

    fundManager.removeStrategyFromQueue(strategy, {"from": keeper})

    tx = fundManager.revokeStrategy(strategy, {"from": keeper})
    strat = fundManager.strategies(strategy)

    assert not strat["approved"]
    assert tx.events["RevokeStrategy"].values() == [strategy]
