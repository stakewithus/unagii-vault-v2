import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, ethVault, token, admin, user):
    pass


def test_deposit_paused(vault, admin, user):
    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.deposit(1, 0, {"from": user})


def test_deposit_zero(vault, user):
    with brownie.reverts("deposit = 0"):
        vault.deposit(0, 0, {"from": user})


def test_deposit_limit(vault, admin, user):
    vault.setDepositLimit(0, {"from": admin})
    with brownie.reverts("deposit limit"):
        vault.deposit(1, 0, {"from": user, "value": 1})


def test_deposit_min_shares(vault, user):
    with brownie.reverts("shares < min"):
        vault.deposit(1, 100, {"from": user, "value": 1})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    amount=strategy("uint256", exclude=0),
)
def test_deposit(vault, uEth, user, amount):
    def snapshot():
        return {
            "eth": {
                "balance": {
                    "user": user.balance(),
                    "vault": vault.balance(),
                },
            },
            "uEth": {
                "balance": {"user": uEth.balanceOf(user)},
                "totalSupply": uEth.totalSupply(),
            },
            "vault": {
                "balanceOfVault": vault.balanceOfVault(),
            },
        }

    # calculate shares to be minted
    calc = vault.calcSharesToMint(amount)

    before = snapshot()
    tx = vault.deposit(amount, 1, {"from": user, "value": amount})
    after = snapshot()

    assert tx.events["Deposit"].values() == [user, amount, amount, calc]

    # token balances
    assert after["token"]["balance"]["user"] == (
        before["token"]["balance"]["user"] - amount
    )
    assert (
        after["token"]["balance"]["vault"]
        == before["token"]["balance"]["vault"] + amount
    )
    assert after["vault"]["balanceOfVault"] == after["token"]["balance"]["vault"]
    assert after["uEth"]["balance"]["user"] > before["uEth"]["balance"]["user"]
