import brownie
from brownie import ZERO_ADDRESS
import pytest


N = 3  # number of active strategies


def test_migrate(FundManager, token, guardian, worker, admin, user, TestStrategy):
    fundManager = FundManager.deploy(
        token, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )

    newFundManager = FundManager.deploy(
        token, guardian, worker, fundManager, {"from": admin}
    )

    timeLock = fundManager.timeLock()

    # test not time lock
    with brownie.reverts("!time lock"):
        fundManager.migrate(newFundManager, {"from": user})

    # test not initialized
    with brownie.reverts("!initialized"):
        fundManager.migrate(newFundManager, {"from": timeLock})

    fundManager.initialize({"from": timeLock})

    # set balance of fund manager > 0
    token.mint(fundManager, 10000)
    token.approve(fundManager, 10000, {"from": fundManager})

    strats = []
    debts = []
    for i in range(N):
        strat = TestStrategy.deploy(fundManager, token, {"from": admin})
        fundManager.approveStrategy(strat, {"from": fundManager.timeLock()})

        debtRatio = i + 1
        minBorrow = (i + 1) * 10
        maxBorrow = (i + 1) * 100
        fundManager.addStrategyToQueue(
            strat, debtRatio, minBorrow, maxBorrow, {"from": admin}
        )

        debt = (i + 1) * 1000
        fundManager.borrow(debt, {"from": strat})

        debts.append(debt)
        strats.append(strat)

    # test not initialized
    fundManager.setPause(False, {"from": admin})
    with brownie.reverts("!paused"):
        fundManager.migrate(newFundManager, {"from": timeLock})

    fundManager.setPause(True, {"from": admin})

    # test fund manager token != token
    _fundManager = FundManager.deploy(
        ZERO_ADDRESS, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    _newFundManager = FundManager.deploy(
        ZERO_ADDRESS, guardian, worker, _fundManager, {"from": admin}
    )

    with brownie.reverts("new fund manager token != token"):
        fundManager.migrate(_newFundManager, {"from": timeLock})

    # test strategy fund manager != new fund manager
    with brownie.reverts("strategy fund manager != new fund manager"):
        fundManager.migrate(newFundManager, {"from": timeLock})

    for strat in strats:
        strat.setFundManager(newFundManager, {"from": strat.timeLock()})

    # test migrate
    def snapshot():
        return {
            "token": {
                "old": token.balanceOf(fundManager),
                "new": token.balanceOf(newFundManager),
            },
            "old": {
                "totalDebt": fundManager.totalDebt(),
            },
            "new": {
                "totalDebt": newFundManager.totalDebt(),
            },
        }

    before = snapshot()
    tx = fundManager.migrate(newFundManager, {"fromm": timeLock})
    after = snapshot()

    assert tx.events["Migrate"].values() == [
        newFundManager,
        before["token"]["old"],
        before["old"]["totalDebt"],
    ]

    assert before["token"]["old"] > 0
    assert after["token"]["old"] == 0
    assert after["token"]["new"] == before["token"]["old"]

    assert after["old"]["totalDebt"] == 0

    for i in range(N):
        addr = fundManager.queue(i)
        strat = fundManager.strategies(addr)
        assert strat["debt"] == 0
