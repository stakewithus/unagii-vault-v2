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
def keeper(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def guardian(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def worker(accounts):
    yield accounts[3]


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
def vault(Vault, token, uToken, admin, guardian, keeper):
    vault = Vault.deploy(token, uToken, guardian, keeper, {"from": admin})
    yield vault


@pytest.fixture(scope="module")
def fundManager(FundManager, testVault, token, admin, guardian, keeper, worker):
    fundManager = FundManager.deploy(token, guardian, keeper, worker, {"from": admin})
    yield fundManager


@pytest.fixture(scope="module")
def setup(chain):
    # uToken - set minter to vault
    uToken.setMinter(vault, {"from": admin})

    # uToken - set admin to time lock
    uToken.setNextAdmin(timeLock, {"from": admin})

    timeLock.queue(uToken, "accept admin")
    chain.sleep(24 * 3600)
    timeLock.exec(uToken, "accept admin")

    # fund manager - set vault
    fundManager.setVault(vault, {"from": admin})

    # fund manager - set admin to time lock
    fundManager.setNextAdmin(timeLock, {"from": admin})

    timeLock.queue(fundManager, "accept admin")
    chain.sleep(24 * 3600)
    timeLock.exec(fundManager, "accept admin")

    # vault - set fund manager
    vault.setFundManager(fundManager, {"from": admin})

    # vault - setup
    vault.setPause(False, {"from": admin})
    vault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    # vault - set admin to time lock
    vault.setNextAdmin(timeLock, {"from": admin})

    timeLock.queue(vault, "accept admin")
    chain.sleep(24 * 3600)
    timeLock.exec(vault, "accept admin")
