import pytest
from brownie import accounts, Vault, UnagiiToken, TestToken


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def timeLock(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def guardian(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def keeper(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def minter(accounts):
    yield accounts[4]


@pytest.fixture(scope="session")
def attacker(accounts):
    yield accounts[5]


@pytest.fixture(scope="module")
def token(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


@pytest.fixture(scope="module")
def uToken(UnagiiToken, token, minter):
    yield UnagiiToken.deploy(token, {"from": minter})


@pytest.fixture(scope="module")
def vault(Vault, token, uToken, admin, timeLock, guardian, keeper):
    yield Vault.deploy(token, uToken, timeLock, guardian, keeper, {"from": admin})