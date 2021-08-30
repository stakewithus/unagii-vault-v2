import pytest
from brownie import (
    accounts,
    Vault,
    EthVault,
    UnagiiToken,
    TimeLock,
    FundManager,
    EthFundManager,
    StrategyTest,
    StrategyEthTest,
    TestToken,
    TestVault,
    TestEthVault,
    TestFundManager,
    TestEthFundManager,
    TestStrategy,
    TestStrategyEth,
    TxTest,
    ZERO_ADDRESS,
)

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


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
def uEth(UnagiiToken, admin, minter):
    uEth = UnagiiToken.deploy(ETH, {"from": admin})
    uEth.setMinter(minter, {"from": admin})
    yield uEth


@pytest.fixture(scope="module")
def vault(Vault, token, uToken, admin, guardian, worker):
    vault = Vault.deploy(token, uToken, {"from": admin})

    uToken.setMinter(vault, {"from": admin})
    vault.setPause(False, {"from": admin})
    vault.setGuardian(guardian, {"from": admin})
    vault.setWorker(worker, {"from": admin})

    yield vault


@pytest.fixture(scope="module")
def ethVault(EthVault, uEth, admin, guardian):
    ethVault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})

    uEth.setMinter(ethVault, {"from": admin})

    ethVault.setPause(False, {"from": admin})
    ethVault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    ethVault.initialize({"from": admin})
    yield ethVault


@pytest.fixture(scope="module")
def fundManager(FundManager, testVault, token, admin, guardian, worker):
    fundManager = FundManager.deploy(
        token, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.setVault(testVault, {"from": admin})
    fundManager.initialize({"from": admin})
    yield fundManager


@pytest.fixture(scope="module")
def ethFundManager(EthFundManager, testEthVault, admin, guardian, worker):
    ethFundManager = EthFundManager.deploy(
        guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    ethFundManager.setVault(testEthVault, {"from": admin})
    ethFundManager.initialize({"from": admin})
    yield ethFundManager


# test contracts
@pytest.fixture(scope="module")
def token(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


@pytest.fixture(scope="module")
def strategyTest(StrategyTest, token, testFundManager, admin, treasury):
    strategyTest = StrategyTest.deploy(
        token, testFundManager, treasury, {"from": admin}
    )
    yield strategyTest


@pytest.fixture(scope="module")
def strategyEthTest(StrategyEthTest, testEthFundManager, admin, treasury):
    strategyEthTest = StrategyEthTest.deploy(
        testEthFundManager, treasury, {"from": admin}
    )
    yield strategyEthTest


@pytest.fixture(scope="module")
def txTest(TxTest, admin):
    yield TxTest.deploy({"from": admin})


@pytest.fixture(scope="module")
def testVault(TestVault, token, admin):
    yield TestVault.deploy(token, {"from": admin})


@pytest.fixture(scope="module")
def testEthVault(TestEthVault, admin):
    yield TestEthVault.deploy(ETH, {"from": admin})


@pytest.fixture(scope="module")
def testFundManager(TestFundManager, vault, token, admin):
    yield TestFundManager.deploy(vault, token, {"from": admin})


@pytest.fixture(scope="module")
def testEthFundManager(TestEthFundManager, ethVault, admin):
    yield TestEthFundManager.deploy(ethVault, ETH, {"from": admin})


@pytest.fixture(scope="module")
def testStrategy(TestStrategy, vault, token, admin):
    yield TestStrategy.deploy(vault, token, {"from": admin})


@pytest.fixture(scope="module")
def testStrategyEth(TestStrategyEth, ethFundManager, admin):
    yield TestStrategyEth.deploy(ethFundManager, ETH, {"from": admin})
