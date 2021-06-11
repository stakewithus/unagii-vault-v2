import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, admin, user):
    token.mint(user, 1000)
    token.approve(vault, 1000, {"from": user})


def test_deposit_paused(vault, admin, user):
    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.deposit(1, 0, {"from": user})


def test_deposit_max_uint(vault, token, uToken, user):
    token.approve(vault, 2 ** 256 - 1, {"from": user})
    uBal = uToken.balanceOf(user)
    vault.deposit(2 ** 256 - 1, 1, {"from": user})
    assert uToken.balanceOf(user) > uBal


def test_deposit_zero(vault, user):
    with brownie.reverts("deposit = 0"):
        vault.deposit(0, 0, {"from": user})


def test_deposit_limit(vault, admin, user):
    vault.setDepositLimit(0, {"from": admin})
    with brownie.reverts("deposit limit"):
        vault.deposit(1, 0, {"from": user})


def test_deposit_fee_on_transfer(vault, admin, token, uToken, user):
    # test diff = 0
    amount = 123
    fee = amount
    token.setFeeOnTransfer(fee)
    vault.setFeeOnTransfer(True, {"from": admin})

    token.approve(vault, amount, {"from": user})

    with brownie.reverts("diff = 0"):
        vault.deposit(amount, 0, {"from": user})

    fee = 1
    token.setFeeOnTransfer(fee)

    uBal = uToken.balanceOf(user)
    vault.deposit(amount, 1, {"from": user})

    assert uToken.balanceOf(user) > uBal


def test_deposit_min_shares(vault, user):
    with brownie.reverts("shares < min"):
        vault.deposit(1, 100, {"from": user})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    amount=strategy("uint256", exclude=0),
)
def test_deposit(vault, token, uToken, user, amount):
    def snapshot():
        return {
            "token": {
                "balance": {
                    "user": token.balanceOf(user),
                    "vault": token.balanceOf(vault),
                },
                "totalSupply": token.totalSupply(),
            },
            "uToken": {
                "balance": {"user": uToken.balanceOf(user)},
                "totalSupply": uToken.totalSupply(),
            },
            "vault": {
                "balanceOfVault": vault.balanceOfVault(),
            },
        }

    token.mint(user, amount)
    token.approve(vault, amount, {"from": user})

    before = snapshot()
    vault.deposit(amount, 1, {"from": user})
    after = snapshot()

    # token balances
    assert after["token"]["balance"]["user"] == (
        before["token"]["balance"]["user"] - amount
    )
    assert (
        after["token"]["balance"]["vault"]
        == before["token"]["balance"]["vault"] + amount
    )
    assert after["vault"]["balanceOfVault"] == after["token"]["balance"]["vault"]
    assert after["uToken"]["balance"]["user"] > before["uToken"]["balance"]["user"]
