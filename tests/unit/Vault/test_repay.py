import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, admin, testFundManager, user):
    if vault.fundManager() != testFundManager.address:
        vault.setFundManager(testFundManager, {"from": admin})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    borrow_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    repay_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
)
def test_repay(
    vault, token, testFundManager, user, deposit_amount, borrow_amount, repay_amount
):
    fundManager = testFundManager

    # deposit into vault
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    # borrow
    vault.borrow(borrow_amount, {"from": testFundManager})

    # approve vault
    token.approve(vault, 2 ** 256 - 1, {"from": fundManager})

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
    tx = vault.repay(repay_amount, {"from": fundManager})
    after = snapshot()

    diff = after["token"]["vault"] - before["token"]["vault"]
    assert tx.events["Repay"].values() == [fundManager, repay_amount, diff]
    assert diff > 0
    assert after["token"]["fundManager"] == before["token"]["fundManager"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] + diff
    assert after["vault"]["debt"] == before["vault"]["debt"] - diff


def test_repay_not_fund_manager(vault, user):
    with brownie.reverts("!fund manager"):
        vault.repay(1, {"from": user})


def test_repay_zero(vault, testFundManager):
    with brownie.reverts("repay = 0"):
        vault.repay(0, {"from": testFundManager})
