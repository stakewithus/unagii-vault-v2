import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_deposit_paused(ethVault, admin, user):
    vault = ethVault

    vault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        vault.deposit(0, {"from": user, "value": 1})


def test_deposit_zero(ethVault, user):
    vault = ethVault

    with brownie.reverts("deposit = 0"):
        vault.deposit(0, {"from": user})


def test_deposit_min_shares(ethVault, user):
    vault = ethVault

    with brownie.reverts("shares < min"):
        vault.deposit(100, {"from": user, "value": 1})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    amount=strategy("uint256", exclude=0, max_value=1000),
)
def test_deposit(ethVault, uEth, user, amount):
    vault = ethVault

    def snapshot():
        return {
            "token": {
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
                "totalAssets": vault.totalAssets(),
                "totalDebt": vault.totalDebt(),
            },
        }

    # calculate shares to be minted
    calc = vault.calcSharesToMint(amount)

    before = snapshot()
    tx = vault.deposit(calc, {"from": user, "value": amount})
    after = snapshot()

    assert tx.events["Deposit"].values() == [user, amount, calc]

    # token balances
    assert after["token"]["balance"]["user"] == (
        before["token"]["balance"]["user"] - amount
    )
    assert (
        after["token"]["balance"]["vault"]
        == before["token"]["balance"]["vault"] + amount
    )
    assert (
        after["vault"]["totalAssets"]
        == after["token"]["balance"]["vault"] + after["vault"]["totalDebt"]
    )
    assert after["uEth"]["balance"]["user"] > before["uEth"]["balance"]["user"]
