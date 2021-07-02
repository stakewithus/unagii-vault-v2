import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, ethVault, admin, user):
    pass


def test_deposit_paused(ethVault, admin, user):
    ethVault.setPause(True, {"from": admin})
    with brownie.reverts("paused"):
        ethVault.deposit(1, 0, {"from": user})


def test_deposit_zero(ethVault, user):
    with brownie.reverts("deposit = 0"):
        ethVault.deposit(0, 0, {"from": user})


def test_deposit_limit(ethVault, admin, user):
    ethVault.setDepositLimit(0, {"from": admin})
    with brownie.reverts("deposit limit"):
        ethVault.deposit(1, 0, {"from": user, "value": 1})


def test_deposit_min_shares(ethVault, user):
    with brownie.reverts("shares < min"):
        ethVault.deposit(1, 100, {"from": user, "value": 1})


@given(
    user=strategy("address", exclude=ZERO_ADDRESS),
    amount=strategy("uint256", min_value=1, max_value=100),
)
def test_deposit(ethVault, uEth, user, amount):
    vault = ethVault

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

    assert tx.events["Deposit"].values() == [user, amount, calc]

    # ETH balances
    assert after["eth"]["balance"]["user"] == (
        before["eth"]["balance"]["user"] - amount
    )
    assert (
        after["eth"]["balance"]["vault"] == before["eth"]["balance"]["vault"] + amount
    )
    assert after["vault"]["balanceOfVault"] == after["eth"]["balance"]["vault"]
    assert after["uEth"]["balance"]["user"] > before["uEth"]["balance"]["user"]
