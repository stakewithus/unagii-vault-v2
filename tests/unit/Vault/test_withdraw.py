import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, admin, user):
    token.mint(user, 1000)
    token.approve(vault, 1000, {"from": user})
    vault.deposit(1000, 1, {"from": user})


def test_withdraw_zero_shares(vault, user):
    with brownie.reverts("shares = 0"):
        vault.withdraw(0, 0, {"from": user})


def test_withdraw_min(vault, user):
    with brownie.reverts("amount < min"):
        vault.withdraw(1, 1000, {"from": user})


def test_withdraw_fee_on_transfer(vault, token, uToken, user):
    shares = 123
    fee = 1
    token.setFeeOnTransfer(fee)

    def snapshot():
        return {
            "token": {"vault": token.balanceOf(vault)},
            "uToken": {"user": uToken.balanceOf(user)},
            "vault": {"balanceOfVault": vault.balanceOfVault()},
        }

    before = snapshot()
    vault.withdraw(shares, 1, {"from": user})
    after = snapshot()

    assert after["uToken"]["user"] < before["uToken"]["user"]
    assert (before["vault"]["balanceOfVault"] - after["vault"]["balanceOfVault"]) == (
        before["token"]["vault"] - after["token"]["vault"]
    )


@given(
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    shares=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    user=strategy("address", exclude=ZERO_ADDRESS),
)
def test_withdraw(vault, token, uToken, user, deposit_amount, shares):
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "user": token.balanceOf(user),
            },
            "uToken": {
                "user": uToken.balanceOf(user),
                "totalSupply": uToken.totalSupply(),
            },
            "vault": {"balanceOfVault": vault.balanceOfVault()},
        }

    before = snapshot()
    vault.withdraw(shares, 1, {"from": user})
    after = snapshot()

    diff = before["token"]["vault"] - after["token"]["vault"]
    assert after["token"]["user"] == before["token"]["user"] + diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
    uDiff = before["uToken"]["user"] - after["uToken"]["user"]
    assert uDiff > 0
    assert after["uToken"]["totalSupply"] == before["uToken"]["totalSupply"] - uDiff
