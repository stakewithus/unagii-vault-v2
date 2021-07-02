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
    repay_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
)
def test_repay(
    ethVault,
    testEthFundManager,
    user,
    deposit_amount,
    borrow_amount,
    repay_amount,
):
    vault = ethVault
    fundManager = testEthFundManager

    # deposit into vault
    vault.deposit(deposit_amount, 1, {"from": user, "value": deposit_amount})

    # borrow
    vault.borrow(borrow_amount, {"from": fundManager})

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
    tx = vault.repay(repay_amount, {"from": fundManager})
    after = snapshot()

    diff = after["eth"]["vault"] - before["eth"]["vault"]
    assert tx.events["Repay"].values() == [fundManager, repay_amount, diff]
    assert diff > 0
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] + diff
    assert after["vault"]["debt"] == before["vault"]["debt"] - diff


def test_repay_not_fund_manager(ethVault, user):
    with brownie.reverts("!fund manager"):
        ethVault.repay(1, {"from": user})


def test_repay_zero(ethVault, testEthFundManager):
    with brownie.reverts("repay = 0"):
        ethVault.repay(0, {"from": testEthFundManager})
