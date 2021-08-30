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


def test_deposit_zero(vault, user):
    with brownie.reverts("deposit = 0"):
        vault.deposit(0, 0, {"from": user})


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

    # calculate shares to be minted
    calc = vault.calcSharesToMint(amount)

    before = snapshot()
    tx = vault.deposit(amount, calc, {"from": user})
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
    assert after["uToken"]["balance"]["user"] > before["uToken"]["balance"]["user"]
