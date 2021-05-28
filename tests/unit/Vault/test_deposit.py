import brownie
from brownie.test import given, strategy
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, admin, user):
    vault.setPause(False, {"from": admin})
    vault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    token.mint(user, 1000)
    token.approve(vault, 1000, {"from": user})


def test_deposit(vault, token, uToken, user):
    amount = 1

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
                "balanceInVault": vault.balanceInVault(),
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
    assert after["vault"]["balanceInVault"] == after["token"]["balance"]["vault"]
    assert after["uToken"]["balance"]["user"] == amount


def test_deposit_paused(accounts, vault, admin):
    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.deposit(1, 0, {"from": accounts[0]})


def test_deposit_max_uint(vault, uToken, user):
    uBal = uToken.balanceOf(user)
    vault.deposit(2 ** 256 - 1, 1, {"from": user})
    assert uToken.balanceOf(user) > uBal


def test_deposit_limit(accounts, vault, admin):
    vault.setDepositLimit(0, {"from": admin})
    with brownie.reverts("deposit limit"):
        vault.deposit(1, 0, {"from": accounts[0]})


def test_deposit_fee_on_transfer(vault, admin, token, uToken, user):
    vault.setFeeOnTransfer(True, {"from": admin})
    fee = 1
    token.setFeeOnTransfer(fee)

    amount = 123

    uBal = uToken.balanceOf(user)
    vault.deposit(amount, 1, {"from": user})

    assert uToken.balanceOf(user) == uBal + amount - fee


def test_deposit_zero(vault, user):
    with brownie.reverts("deposit = 0"):
        vault.deposit(0, 0, {"from": user})


def test_deposit_min_shares(vault, user):
    amount = 123
    with brownie.reverts("shares < min"):
        vault.deposit(amount, amount + 1, {"from": user})
