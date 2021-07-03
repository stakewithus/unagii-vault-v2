import brownie
from brownie import ZERO_ADDRESS
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

N = 3  # number of active strategies


def test_migrate(EthFundManager, guardian, worker, admin, user, TestStrategyEth):
    fundManager = EthFundManager.deploy(guardian, worker, ZERO_ADDRESS, {"from": admin})

    newFundManager = EthFundManager.deploy(
        guardian, worker, fundManager, {"from": admin}
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
    user.transfer(fundManager, 10000)

    strats = []
    debts = []
    for i in range(N):
        strat = TestStrategyEth.deploy(fundManager, ETH, {"from": admin})
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

    # test strategy fund manager != new fund manager
    with brownie.reverts("strategy fund manager != new fund manager"):
        fundManager.migrate(newFundManager, {"from": timeLock})

    for strat in strats:
        strat.setFundManager(newFundManager, {"from": strat.timeLock()})

    # test migrate
    def snapshot():
        return {
            "eth": {"old": fundManager.balance(), "new": newFundManager.balance()},
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
        before["eth"]["old"],
        before["old"]["totalDebt"],
    ]

    assert before["eth"]["old"] > 0
    assert after["eth"]["old"] == 0
    assert after["eth"]["new"] == before["eth"]["old"]

    assert after["old"]["totalDebt"] == 0

    for i in range(N):
        addr = fundManager.queue(i)
        strat = fundManager.strategies(addr)
        assert strat["debt"] == 0
