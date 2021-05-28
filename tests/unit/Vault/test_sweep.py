import brownie
import pytest


@pytest.fixture
def anotherToken(TestToken, admin):
    yield TestToken.deploy("test", "TEST", 18, {"from": admin})


def test_sweep(accounts, vault, token, anotherToken, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.sweep(token, {"from": user})

    # protected token
    with brownie.reverts("protected"):
        vault.sweep(token, {"from": admin})

    vault.sweep(anotherToken, {"from": admin})
