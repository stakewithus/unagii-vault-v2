import pytest
from brownie import (
    accounts,
    Vault,
    UnagiiToken,
    TimeLock,
    PerfFeeTest,
    StrategyTest,
    TestToken,
    TestVault,
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
    vault = Vault.deploy(token, uToken, guardian, worker, {"from": admin})

    uToken.setMinter(vault, {"from": admin})
    vault.setPause(False, {"from": admin})
    vault.setBlockDelay(1, {"from": admin})

    yield vault


@pytest.fixture(scope="module")
def ethVault(EthVault, uEth, admin, guardian, worker):
    ethVault = EthVault.deploy(uEth, guardian, worker, {"from": admin})

    uEth.setMinter(ethVault, {"from": admin})
    ethVault.setPause(False, {"from": admin})
    ethVault.setBlockDelay(1, {"from": admin})

    # allow admin to send ETH
    ethVault.setWhitelist(admin, True, {"from": admin})

    yield ethVault


# test contracts
@pytest.fixture(scope="module")
def token(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


@pytest.fixture(scope="module")
def perfFeeTest(PerfFeeTest, admin):
    yield PerfFeeTest.deploy({"from": admin})


@pytest.fixture(scope="module")
def strategyTest(StrategyTest, token, testVault, admin, treasury):
    minProfit = 10 ** token.decimals()
    maxProfit = 1000 * 10 ** token.decimals()
    strategyTest = StrategyTest.deploy(
        token, testVault, treasury, minProfit, maxProfit, {"from": admin}
    )
    yield strategyTest


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
def testStrategy(TestStrategy, vault, token, admin):
    yield TestStrategy.deploy(vault, token, {"from": admin})


@pytest.fixture(scope="module")
def testStrategyEth(TestStrategyEth, ethVault, admin):
    yield TestStrategyEth.deploy(ethVault, {"from": admin})
