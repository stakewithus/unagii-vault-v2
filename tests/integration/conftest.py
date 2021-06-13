import pytest
from brownie import (
    accounts,
    Vault,
    UnagiiToken,
    TimeLock,
    FundManager,
    TestToken,
    TestStrategy,
)


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def guardian(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def worker(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def attacker(accounts):
    yield accounts[-2]


@pytest.fixture(scope="session")
def user(accounts):
    yield accounts[-1]


@pytest.fixture(scope="module")
def timeLock(TimeLock, admin):
    yield TimeLock.deploy({"from": admin})


@pytest.fixture(scope="module")
def token(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


@pytest.fixture(scope="module")
def uToken(UnagiiToken, token, admin):
    uToken = UnagiiToken.deploy(token, {"from": admin})
    yield uToken


@pytest.fixture(scope="module")
def vault(Vault, token, uToken, admin, guardian):
    vault = Vault.deploy(token, uToken, guardian, {"from": admin})
    yield vault


@pytest.fixture(scope="module")
def fundManager(FundManager, token, admin, guardian, worker):
    fundManager = FundManager.deploy(token, guardian, worker, {"from": admin})
    yield fundManager


# time lock delay
DELAY = 24 * 3600


@pytest.fixture(scope="module")
def setup(chain, uToken, vault, timeLock, fundManager, admin):
    # uToken - set minter to vault
    uToken.setMinter(vault, {"from": admin})

    # uToken - set next time lock
    uToken.setNextTimeLock(timeLock, {"from": admin})

    data = uToken.acceptTimeLock.encode_input()
    tx = timeLock.queue(uToken, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(uToken, 0, data, eta, 0, {"from": admin})

    # fund manager - set vault
    fundManager.setVault(vault, {"from": admin})

    # fund manager - set time lock
    fundManager.setNextTimeLock(timeLock, {"from": admin})

    data = fundManager.acceptTimeLock.encode_input()
    tx = timeLock.queue(fundManager, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(fundManager, 0, data, eta, 0, {"from": admin})

    # vault - set fund manager
    vault.setFundManager(fundManager, {"from": admin})

    # vault - setup
    vault.setPause(False, {"from": admin})
    vault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    # vault - set admin to time lock
    vault.setNextTimeLock(timeLock, {"from": admin})

    data = vault.acceptTimeLock.encode_input()
    tx = timeLock.queue(vault, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(vault, 0, data, eta, 0, {"from": admin})
