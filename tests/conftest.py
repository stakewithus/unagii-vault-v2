import pytest
from brownie import accounts, UnagiiToken, TestToken


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def minter(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def attacker(accounts):
    yield accounts[1]


@pytest.fixture(scope="module")
def token(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


@pytest.fixture(scope="module")
def uToken(UnagiiToken, token, minter):
    yield UnagiiToken.deploy(token, {"from": minter})