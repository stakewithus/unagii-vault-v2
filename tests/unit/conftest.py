import pytest
from brownie import (
    accounts,
    Vault,
    UnagiiToken,
    TimeLock,
    FundManager,
    StrategyTest,
    TestToken,
    TestVault,
    TestFundManager,
    TestStrategy,
    TxTest,
    ZERO_ADDRESS,
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
def minter(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def treasury(accounts):
    yield accounts[4]


@pytest.fixture(scope="session")
def attacker(accounts):
    yield accounts[-2]


@pytest.fixture(scope="session")
def user(accounts):
    yield accounts[-1]


# Unagii contracts
@pytest.fixture(scope="module")
def timeLock(TimeLock, admin):
    yield TimeLock.deploy({"from": admin})


@pytest.fixture(scope="module")
def uToken(UnagiiToken, token, admin, minter):
    uToken = UnagiiToken.deploy(token, {"from": admin})
    uToken.setMinter(minter, {"from": admin})
    yield uToken


@pytest.fixture(scope="module")
def vault(Vault, token, uToken, admin, guardian):
    vault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})

    uToken.setMinter(vault, {"from": admin})

    vault.setPause(False, {"from": admin})
    vault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    vault.initialize({"from": admin})
    yield vault


@pytest.fixture(scope="module")
def fundManager(FundManager, testVault, token, admin, guardian, worker):
    fundManager = FundManager.deploy(
        token, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.setVault(testVault, {"from": admin})
    fundManager.initialize({"from": admin})
    yield fundManager


# test contracts
@pytest.fixture(scope="module")
def token(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


@pytest.fixture(scope="module")
def strategyTest(StrategyTest, testFundManager, admin, guardian, worker, treasury):
    strategyTest = StrategyTest.deploy(
        testFundManager, guardian, worker, treasury, {"from": admin}
    )
    yield strategyTest


@pytest.fixture(scope="module")
def txTest(TxTest, admin):
    yield TxTest.deploy({"from": admin})


@pytest.fixture(scope="module")
def testVault(TestVault, token, admin):
    yield TestVault.deploy(token, {"from": admin})


@pytest.fixture(scope="module")
def testFundManager(TestFundManager, vault, token, admin):
    yield TestFundManager.deploy(vault, token, {"from": admin})


@pytest.fixture(scope="module")
def testStrategy(TestStrategy, fundManager, token, admin):
    yield TestStrategy.deploy(fundManager, token, {"from": admin})
