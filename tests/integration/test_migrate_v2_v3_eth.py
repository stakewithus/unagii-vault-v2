import brownie
from brownie import (
    ZERO_ADDRESS,
    V2EthVault,
    V2EthFundManager,
    V2StrategyEthTest,
    StrategyMigrateEth,
    EthVault,
)
import pytest

# TODO: mainnet test

DELAY = 24 * 3600
N = 3  # number of active strategies


@pytest.fixture(scope="module")
def v2(uEth, admin):
    yield V2EthVault.deploy(uEth, ZERO_ADDRESS, ZERO_ADDRESS, {"from": admin})


@pytest.fixture(scope="module")
def fundManager(admin):
    yield V2EthFundManager.deploy(
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, {"from": admin}
    )


@pytest.fixture(scope="module")
def v2_setup(chain, v2, fundManager, uEth, timeLock, admin, user):
    uEth.setMinter(v2, {"from": admin})

    # uEth set time lock
    uEth.setNextTimeLock(timeLock, {"from": admin})
    uEth.acceptTimeLock({"from": timeLock})

    fundManager.setVault(v2, {"from": admin})
    fundManager.initialize({"from": admin})

    # fund manager set time lock
    fundManager.setNextTimeLock(timeLock, {"from": admin})
    fundManager.acceptTimeLock({"from": timeLock})

    v2.setFundManager(fundManager, {"from": admin})

    v2.setPause(False, {"from": admin})
    v2.setDepositLimit(2 ** 256 - 1, {"from": admin})
    v2.initialize({"from": admin})

    v2.setNextTimeLock(timeLock, {"from": admin})
    v2.acceptTimeLock({"from": timeLock})

    # activate strategies
    strats = []
    for i in range(N):
        strat = V2StrategyEthTest.deploy(fundManager, admin, {"from": admin})

        # set time lock
        strat.setNextTimeLock(timeLock, {"from": admin})
        strat.acceptTimeLock({"from": timeLock})

        # this will be time locked on mainnet
        fundManager.approveStrategy(strat, {"from": timeLock})

        fundManager.addStrategyToQueue(strat, 100, 0, 2 ** 256 - 1, {"from": admin})
        strats.append(strat)

    # deposit
    v2.deposit(1000, 1000, {"from": user, "value": 1000})

    # deposit strategies
    fundManager.borrowFromVault(2 ** 256 - 1, 1, {"from": admin})

    for strat in strats:
        strat.deposit(2 ** 256 - 1, 1, {"from": admin})


@pytest.fixture(scope="module")
def v3(uEth, admin):
    yield EthVault.deploy(uEth, ZERO_ADDRESS, ZERO_ADDRESS, {"from": admin})


@pytest.fixture(scope="module")
def v3_setup(chain, timeLock, v3, admin):
    v3.setNextTimeLock(timeLock, {"from": admin})

    data = v3.acceptTimeLock.encode_input()
    tx = timeLock.queue(v3, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(v3, 0, data, eta, 0, {"from": admin})


@pytest.fixture(scope="module")
def strategyMigrate(chain, fundManager, v2, v3, admin):
    yield StrategyMigrateEth.deploy(fundManager, admin, v2, v3, {"from": admin})


def test_migrate_v2_v3(
    chain,
    uEth,
    admin,
    timeLock,
    v2_setup,
    v2,
    fundManager,
    v3,
    v3_setup,
    strategyMigrate,
):
    assert v2.timeLock() == timeLock
    assert v2.admin() == admin
    assert not v2.paused()
    assert uEth.minter() == v2

    assert fundManager.timeLock() == timeLock
    assert fundManager.admin() == admin

    assert v3.timeLock() == timeLock
    assert v3.admin() == admin
    assert v3.paused()

    # allow strategy migrate to send ETH to v3
    v3.setWhitelist(strategyMigrate, True, {"from": admin})

    # withdraw from strategies
    for i in range(N):
        strat = V2StrategyEthTest.at(fundManager.queue(i))
        strat.repay(strat.balance(), 1, {"from": admin})

    # deactivate strategies
    for i in range(N):
        strat = V2StrategyEthTest.at(fundManager.queue(0))
        fundManager.removeStrategyFromQueue(strat, {"from": admin})

    # set time lock on strategy migrate
    strategyMigrate.setNextTimeLock(timeLock, {"from": admin})
    strategyMigrate.acceptTimeLock({"from": timeLock})

    # approve and activate strategy migrate
    fundManager.approveStrategy(strategyMigrate, {"from": timeLock})

    fundManager.addStrategyToQueue(
        strategyMigrate, 100, 0, 2 ** 256 - 1, {"from": admin}
    )

    v2.setMinReserve(0, {"from": admin})

    assert v2.calcMaxBorrow() == v2.balance()

    def snapshot():
        return {
            "v2": {
                "totalAssets": v2.totalAssets(),
                "debt": v2.debt(),
            },
            "token": {
                "v2": v2.balance(),
                "v3": v3.balance(),
                "fundManager": fundManager.balance(),
                "strategyMigrate": strategyMigrate.balance(),
            },
        }

    # time lock migration
    targets = [
        fundManager,
        v2,
        strategyMigrate,
        uEth,
    ]
    values = [0, 0, 0, 0]
    data = [
        fundManager.borrowFromVault.encode_input(2 ** 256 - 1, 1),
        v2.setPause.encode_input(True),
        strategyMigrate.migrateToV3.encode_input(),
        uEth.setMinter.encode_input(v3),
    ]
    delays = [
        DELAY,
        DELAY,
        DELAY,
        DELAY,
    ]
    nonces = [0, 0, 0, 0]

    tx = timeLock.batchQueue(targets, values, data, delays, nonces, {"from": admin})
    eta = tx.timestamp + DELAY

    chain.sleep(DELAY)

    # execute time lock
    etas = [eta, eta, eta, eta]
    before = snapshot()
    tx = timeLock.batchExecute(targets, values, data, etas, nonces, {"from": admin})
    after = snapshot()

    assert before["v2"]["totalAssets"] > 0
    assert before["token"]["v2"] > 0
    assert before["token"]["fundManager"] > 0
    assert before["token"]["fundManager"] >= before["v2"]["debt"]
    assert before["token"]["strategyMigrate"] == 0
    assert before["token"]["v3"] == 0

    assert after["token"]["v2"] == 0
    assert after["token"]["fundManager"] == 0
    assert after["token"]["strategyMigrate"] == 0
    assert after["token"]["v3"] == before["v2"]["totalAssets"]

    assert v2.paused()
    assert uEth.minter() == v3
