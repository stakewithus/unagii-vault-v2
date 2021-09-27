import brownie
from brownie import (
    ZERO_ADDRESS,
    V2Vault,
    V2FundManager,
    V2StrategyTest,
    StrategyMigrate,
    Vault,
)
import pytest

# TODO: mainnet test

DELAY = 24 * 3600
N = 3  # number of active strategies


@pytest.fixture(scope="module")
def v2(token, uToken, admin):
    yield V2Vault.deploy(token, uToken, ZERO_ADDRESS, ZERO_ADDRESS, {"from": admin})


@pytest.fixture(scope="module")
def fundManager(token, admin):
    yield V2FundManager.deploy(
        token, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, {"from": admin}
    )


@pytest.fixture(scope="module")
def v2_setup(chain, v2, fundManager, token, uToken, timeLock, admin, user):
    uToken.setMinter(v2, {"from": admin})

    # uToken set time lock
    uToken.setNextTimeLock(timeLock, {"from": admin})
    uToken.acceptTimeLock({"from": timeLock})

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
        strat = V2StrategyTest.deploy(token, fundManager, admin, {"from": admin})

        # set time lock
        strat.setNextTimeLock(timeLock, {"from": admin})
        strat.acceptTimeLock({"from": timeLock})

        # this will be time locked on mainnet
        fundManager.approveStrategy(strat, {"from": timeLock})

        fundManager.addStrategyToQueue(strat, 100, 0, 2 ** 256 - 1, {"from": admin})
        strats.append(strat)

    # deposit
    token.mint(user, 1000)
    token.approve(v2, 1000, {"from": user})
    v2.deposit(1000, 1000, {"from": user})

    # deposit strategies
    fundManager.borrowFromVault(2 ** 256 - 1, 1, {"from": admin})

    for strat in strats:
        strat.deposit(2 ** 256 - 1, 1, {"from": admin})


@pytest.fixture(scope="module")
def v3(token, uToken, admin):
    yield Vault.deploy(token, uToken, ZERO_ADDRESS, ZERO_ADDRESS, {"from": admin})


@pytest.fixture(scope="module")
def v3_setup(chain, timeLock, v3, admin):
    v3.setNextTimeLock(timeLock, {"from": admin})

    target = v3
    data = v3.acceptTimeLock.encode_input()
    tx = timeLock.queue(target, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(target, 0, data, eta, 0, {"from": admin})


@pytest.fixture(scope="module")
def strategyMigrate(chain, token, fundManager, v2, v3, admin):
    yield StrategyMigrate.deploy(token, fundManager, admin, v2, v3, {"from": admin})


def test_migrate_v2_v3(
    chain,
    token,
    uToken,
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
    assert uToken.minter() == v2

    assert fundManager.timeLock() == timeLock
    assert fundManager.admin() == admin

    assert v3.timeLock() == timeLock
    assert v3.admin() == admin
    assert v3.paused()

    # set time lock on strategy migrate
    strategyMigrate.setNextTimeLock(timeLock, {"from": admin})

    target = strategyMigrate
    data = strategyMigrate.acceptTimeLock.encode_input()
    tx = timeLock.queue(target, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(target, 0, data, eta, 0, {"from": admin})

    # approve and activate strategy migrate
    target = fundManager
    data = fundManager.approveStrategy.encode_input(strategyMigrate)
    tx = timeLock.queue(target, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(target, 0, data, eta, 0, {"from": admin})

    fundManager.addStrategyToQueue(
        strategyMigrate, 100, 0, 2 ** 256 - 1, {"from": admin}
    )

    # withdraw from strategies
    for i in range(N):
        strat = V2StrategyTest.at(fundManager.queue(i))
        strat.repay(2 ** 256 - 1, 1, {"from": admin})

    # deactivate strategies
    for i in range(N):
        strat = V2StrategyTest.at(fundManager.queue(0))
        fundManager.removeStrategyFromQueue(strat, {"from": admin})

    v2.setMinReserve(0, {"from": admin})

    assert v2.calcMaxBorrow() == token.balanceOf(v2)

    def snapshot():
        return {
            "v2": {
                "totalAssets": v2.totalAssets(),
                "debt": v2.debt(),
            },
            "token": {
                "v2": token.balanceOf(v2),
                "v3": token.balanceOf(v3),
                "fundManager": token.balanceOf(fundManager),
                "strategyMigrate": token.balanceOf(strategyMigrate),
            },
        }

    # time lock migration
    targets = [
        fundManager,
        v2,
        strategyMigrate,
        uToken,
    ]
    values = [0, 0, 0, 0]
    data = [
        fundManager.borrowFromVault.encode_input(2 ** 256 - 1, 1),
        v2.setPause.encode_input(True),
        strategyMigrate.migrateToV3.encode_input(),
        uToken.setMinter.encode_input(v3),
    ]
    delays = [DELAY, DELAY, DELAY, DELAY]
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
    assert uToken.minter() == v3
