import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_approve_strategy(fundManager, token, admin, testStrategy, user):
    strategy = testStrategy

    # revert if not time lock
    with brownie.reverts("!admin"):
        fundManager.approveStrategy(strategy, {"from": user})

    # revert if strategy.fundManager != fundManager
    strategy.setFundManager(ZERO_ADDRESS)
    with brownie.reverts("strategy fund manager != this"):
        fundManager.approveStrategy(strategy, {"from": admin})

    strategy.setFundManager(fundManager)

    # revert if strategy.token != token
    strategy.setToken(ZERO_ADDRESS)
    with brownie.reverts("strategy token != token"):
        fundManager.approveStrategy(strategy, {"from": admin})

    strategy.setToken(token)

    tx = fundManager.approveStrategy(strategy, {"from": admin})
    strat = fundManager.strategies(strategy)

    assert strat["approved"]
    assert not strat["active"]
    assert not strat["activated"]
    assert strat["debtRatio"] == 0
    assert strat["debt"] == 0
    assert strat["minBorrow"] == 0
    assert strat["maxBorrow"] == 0

    assert tx.events["ApproveStrategy"].values() == [strategy]

    # revert if approved
    with brownie.reverts("approved"):
        fundManager.approveStrategy(strategy, {"from": admin})
