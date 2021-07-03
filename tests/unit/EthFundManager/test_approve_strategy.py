import brownie
from brownie import ZERO_ADDRESS
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_approve_strategy(ethFundManager, testStrategyEth, user):
    fundManager = ethFundManager
    strategy = testStrategyEth
    timeLock = fundManager.timeLock()

    # revert if not time lock
    with brownie.reverts("!time lock"):
        fundManager.approveStrategy(strategy, {"from": user})

    # revert if strategy.token != token
    strategy.setToken(ZERO_ADDRESS)
    with brownie.reverts("strategy token != ETH"):
        fundManager.approveStrategy(strategy, {"from": timeLock})

    strategy.setToken(ETH)

    # revert if strategy.fundManager != fundManager
    strategy.setFundManager(ZERO_ADDRESS)
    with brownie.reverts("strategy fund manager != this"):
        fundManager.approveStrategy(strategy, {"from": timeLock})

    strategy.setFundManager(fundManager)

    tx = fundManager.approveStrategy(strategy, {"from": timeLock})
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
        fundManager.approveStrategy(strategy, {"from": timeLock})
