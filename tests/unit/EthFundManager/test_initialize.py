import brownie
from brownie import ZERO_ADDRESS
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_initialize_no_old_fund_manager(EthFundManager, guardian, worker, admin, user):
    fundManager = EthFundManager.deploy(guardian, worker, ZERO_ADDRESS, {"from": admin})

    # test not authorized
    with brownie.reverts("!auth"):
        fundManager.initialize({"from": user})

    fundManager.initialize({"from": admin})
    assert fundManager.initialized()

    # test already initialized
    with brownie.reverts("initialized"):
        fundManager.initialize({"from": admin})


N = 3  # number of active strategies in old fund manager


def test_initialize_with_old_fund_manager(
    EthFundManager, guardian, worker, admin, user, testEthVault, TestStrategyEth
):
    vault = testEthVault

    oldFundManager = EthFundManager.deploy(
        guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    oldFundManager.initialize({"from": admin})

    fundManager = EthFundManager.deploy(
        guardian, worker, oldFundManager, {"from": admin}
    )

    # set balance of old fund manager > 0
    user.transfer(oldFundManager, 10000)

    strats = []
    debtRatios = []
    minBorrows = []
    maxBorrows = []
    debts = []
    for i in range(N):
        strat = TestStrategyEth.deploy(oldFundManager, ETH, {"from": admin})
        oldFundManager.approveStrategy(strat, {"from": oldFundManager.timeLock()})

        debtRatio = i + 1
        minBorrow = (i + 1) * 10
        maxBorrow = (i + 1) * 100
        oldFundManager.addStrategyToQueue(
            strat, debtRatio, minBorrow, maxBorrow, {"from": oldFundManager.timeLock()}
        )

        debt = (i + 1) * 1000
        oldFundManager.borrow(debt, {"from": strat})

        debtRatios.append(debtRatio)
        minBorrows.append(minBorrow)
        maxBorrows.append(maxBorrow)
        debts.append(debt)

        strats.append(strat)

    # test not old fund manager
    with brownie.reverts("!old fund manager"):
        fundManager.initialize({"from": user})

    # test old fund manager vault != vault
    oldFundManager.setVault(vault)

    with brownie.reverts("old fund manager vault != vault"):
        fundManager.initialize({"from": oldFundManager})

    fundManager.setVault(vault)

    # test strategy fund manager != self
    with brownie.reverts("strategy fund manager != self"):
        fundManager.initialize({"from": oldFundManager})

    for strat in strats:
        strat.setFundManager(fundManager, {"from": strat.timeLock()})

    # test initialize
    def snapshot():
        return {
            "eth": {
                "old": oldFundManager.balance(),
                "new": fundManager.balance(),
            },
            "old": {
                "totalDebt": oldFundManager.totalDebt(),
                "totalDebtRatio": oldFundManager.totalDebtRatio(),
                "queue": [oldFundManager.queue(i) for i in range(N)],
            },
            "new": {
                "totalDebt": fundManager.totalDebt(),
                "totalDebtRatio": fundManager.totalDebtRatio(),
                "queue": [fundManager.queue(i) for i in range(N)],
            },
        }

    before = snapshot()
    fundManager.initialize({"from": oldFundManager, "value": oldFundManager.balance()})
    after = snapshot()

    assert fundManager.initialized()

    assert before["eth"]["old"] > 0
    assert after["eth"]["old"] == 0
    assert after["eth"]["new"] == before["eth"]["old"]

    assert after["new"]["totalDebt"] == before["old"]["totalDebt"]
    assert after["new"]["totalDebtRatio"] == before["old"]["totalDebtRatio"]
    assert after["new"]["queue"] == before["old"]["queue"]

    for addr in after["new"]["queue"]:
        assert fundManager.strategies(addr) == oldFundManager.strategies(addr)
