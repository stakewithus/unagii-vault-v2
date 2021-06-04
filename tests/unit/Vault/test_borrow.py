import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, timeLock, testFundManager, user):
    if vault.fundManager() != testFundManager.address:
        vault.setFundManager(testFundManager, {"from": timeLock})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    borrow_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
)
def test_borrow(vault, token, testFundManager, user, deposit_amount, borrow_amount):
    fundManager = testFundManager

    # deposit into vault
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "fundManager": token.balanceOf(fundManager),
            },
            "vault": {
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    before = snapshot()
    vault.borrow(borrow_amount, {"from": testFundManager})
    after = snapshot()

    diff = before["token"]["vault"] - after["token"]["vault"]
    assert diff > 0
    assert after["token"]["fundManager"] == before["token"]["fundManager"] + diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
    assert after["vault"]["debt"] == before["vault"]["debt"] + diff


def test_borrow_paused(vault, admin, testFundManager):
    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.borrow(1, {"from": testFundManager})


def test_borrow_not_fund_manager(vault, user):
    with brownie.reverts("!fund manager"):
        vault.borrow(1, {"from": user})


def test_borrow_zero(vault, testFundManager):
    with brownie.reverts("borrow = 0"):
        vault.borrow(0, {"from": testFundManager})