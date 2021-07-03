import brownie
import pytest

DELAY = 24 * 3600
N = 3  # number of active strategies

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_eth_fund_manager_migration(
    chain,
    setup_eth,
    ethVault,
    ethFundManager,
    EthFundManager,
    admin,
    timeLock,
    guardian,
    worker,
    TestStrategyEth,
    user,
):
    vault = ethVault
    fundManager = ethFundManager

    newFundManager = EthFundManager.deploy(
        guardian, worker, fundManager, {"from": admin}
    )
    newFundManager.setVault(vault, {"from": admin})

    # setup fund maanger balance > 0
    user.transfer(fundManager, 10000)

    # setup fund maanger strategies
    strats = []
    debts = []
    for i in range(N):
        strat = TestStrategyEth.deploy(fundManager, ETH, {"from": admin})

        # set time lock
        strat.setNextTimeLock(timeLock, {"from": admin})

        data = strat.acceptTimeLock.encode_input()
        tx = timeLock.queue(strat, 0, data, DELAY, 0, {"from": admin})
        eta = tx.timestamp + DELAY
        chain.sleep(DELAY)
        timeLock.execute(strat, 0, data, eta, 0, {"from": admin})

        # this will be time locked on mainnet
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

    # queue txs
    targets = []
    values = []
    data = []
    delays = []
    nonces = []

    # queue set fund manager
    for strat in strats:
        targets.append(strat)
        values.append(0)
        data.append(strat.setFundManager.encode_input(newFundManager))
        delays.append(DELAY)
        nonces.append(0)

    # queue migrate
    targets.append(fundManager)
    values.append(0)
    data.append(fundManager.migrate.encode_input(newFundManager))
    delays.append(DELAY)
    nonces.append(0)

    tx = timeLock.batchQueue(targets, values, data, delays, nonces, {"from": admin})

    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)

    fundManager.setPause(True, {"from": admin})

    def snapshot():
        old_queue = [fundManager.queue(i) for i in range(N)]
        new_queue = [newFundManager.queue(i) for i in range(N)]

        return {
            "eth": {
                "old": fundManager.balance(),
                "new": newFundManager.balance(),
            },
            "old": {
                "totalDebt": fundManager.totalDebt(),
                "totalDebtRatio": fundManager.totalDebtRatio(),
                "queue": old_queue,
                "strats": [fundManager.strategies(addr) for addr in old_queue],
            },
            "new": {
                "totalDebt": newFundManager.totalDebt(),
                "totalDebtRatio": newFundManager.totalDebtRatio(),
                "queue": new_queue,
                "strats": [newFundManager.strategies(addr) for addr in new_queue],
            },
        }

    etas = [eta for _ in delays]

    before = snapshot()
    tx = timeLock.batchExecute(
        targets,
        values,
        data,
        etas,
        nonces,
        {"from": admin},
    )
    after = snapshot()

    assert fundManager.totalDebt() == 0
    assert newFundManager.initialized()

    assert before["eth"]["old"] > 0
    assert after["eth"]["old"] == 0
    assert after["eth"]["new"] == before["eth"]["old"]

    assert after["new"]["totalDebt"] == before["old"]["totalDebt"]
    assert after["new"]["totalDebtRatio"] == before["old"]["totalDebtRatio"]
    assert after["new"]["queue"] == before["old"]["queue"]

    for strat in after["old"]["strats"]:
        assert strat["debt"] == 0

    for i in range(N):
        assert after["new"]["strats"][i] == before["old"]["strats"][i]
