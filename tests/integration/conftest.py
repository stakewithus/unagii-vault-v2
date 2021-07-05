import pytest
from brownie import (
    ZERO_ADDRESS,
    accounts,
    Vault,
    EthVault,
    UnagiiToken,
    TimeLock,
    FundManager,
    EthFundManager,
    TestToken,
    TestStrategy,
    TestStrategyEth,
    TestFlash,
    TestFlashEth,
    TestZap,
    TestZapEth,
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
def attacker(accounts):
    yield accounts[-2]


@pytest.fixture(scope="session")
def user(accounts):
    yield accounts[-1]


@pytest.fixture(scope="session")
def eth_whale(accounts):
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
def uEth(UnagiiToken, admin):
    uEth = UnagiiToken.deploy(ETH, {"from": admin})
    yield uEth


@pytest.fixture(scope="module")
def vault(Vault, token, uToken, admin, guardian):
    vault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})
    yield vault


@pytest.fixture(scope="module")
def ethVault(EthVault, uEth, admin, guardian):
    ethVault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})
    yield ethVault


@pytest.fixture(scope="module")
def fundManager(FundManager, token, admin, guardian, worker):
    fundManager = FundManager.deploy(
        token, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    yield fundManager


@pytest.fixture(scope="module")
def ethFundManager(EthFundManager, admin, guardian, worker):
    ethFundManager = EthFundManager.deploy(
        guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    yield ethFundManager


@pytest.fixture(scope="module")
def flash(TestFlash, token, uToken, vault, attacker):
    flash = TestFlash.deploy(token, uToken, vault, {"from": attacker})
    yield flash


@pytest.fixture(scope="module")
def flashEth(TestFlashEth, uEth, ethVault, attacker):
    flashEth = TestFlashEth.deploy(ETH, uEth, ethVault, {"from": attacker})
    yield flashEth


@pytest.fixture(scope="module")
def zap(TestZap, token, uToken, vault, admin):
    zap = TestZap.deploy(token, uToken, vault, {"from": admin})
    yield zap


@pytest.fixture(scope="module")
def zapEth(TestZapEth, uEth, ethVault, admin):
    zapEth = TestZapEth.deploy(ETH, uEth, ethVault, {"from": admin})
    yield zapEth


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
    fundManager.initialize({"from": admin})

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
    vault.initialize({"from": admin})

    # vault - set admin to time lock
    vault.setNextTimeLock(timeLock, {"from": admin})

    data = vault.acceptTimeLock.encode_input()
    tx = timeLock.queue(vault, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(vault, 0, data, eta, 0, {"from": admin})


@pytest.fixture(scope="module")
def setup_eth(chain, uEth, ethVault, timeLock, ethFundManager, admin):
    uToken = uEth
    vault = ethVault
    fundManager = ethFundManager

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
    fundManager.initialize({"from": admin})

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
    vault.initialize({"from": admin})

    # vault - set admin to time lock
    vault.setNextTimeLock(timeLock, {"from": admin})

    data = vault.acceptTimeLock.encode_input()
    tx = timeLock.queue(vault, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(vault, 0, data, eta, 0, {"from": admin})
