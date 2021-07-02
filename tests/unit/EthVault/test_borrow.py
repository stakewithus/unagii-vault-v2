import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, ethVault, admin, testEthFundManager, user):
    if ethVault.fundManager() != testEthFundManager.address:
        timeLock = ethVault.timeLock()
        ethVault.setFundManager(testEthFundManager, {"from": timeLock})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    deposit_amount=strategy("uint256", min_value=1, max_value=1000),
    borrow_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
)
def test_borrow(ethVault, testEthFundManager, user, deposit_amount, borrow_amount):
    vault = ethVault
    fundManager = testEthFundManager

    # deposit into vault
    vault.deposit(deposit_amount, 1, {"from": user, "value": deposit_amount})

    def snapshot():
        return {
            "eth": {
                "vault": vault.balance(),
                "fundManager": fundManager.balance(),
            },
            "vault": {
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    before = snapshot()
    tx = vault.borrow(borrow_amount, {"from": fundManager})
    after = snapshot()

    diff = before["eth"]["vault"] - after["eth"]["vault"]
    assert tx.events["Borrow"].values() == [fundManager, borrow_amount, diff]
    assert diff > 0
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] + diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
    assert after["vault"]["debt"] == before["vault"]["debt"] + diff


def test_borrow_paused(ethVault, admin, testEthFundManager):
    ethVault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        ethVault.borrow(1, {"from": testEthFundManager})


def test_borrow_not_fund_manager(ethVault, user):
    with brownie.reverts("!fund manager"):
        ethVault.borrow(1, {"from": user})


def test_borrow_zero(ethVault, testEthFundManager):
    with brownie.reverts("borrow = 0"):
        ethVault.borrow(0, {"from": testEthFundManager})