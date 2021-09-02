import brownie
from brownie import ZERO_ADDRESS
from brownie import test
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, chain, vault, token, admin, user):
    token.mint(user, 1000)
    token.approve(vault, 1000, {"from": user})
    vault.deposit(1000, 1, {"from": user})
    chain.mine(vault.blockDelay())


def test_withdraw_zero_shares(vault, user):
    with brownie.reverts("shares = 0"):
        vault.withdraw(0, 0, {"from": user})


def test_withdraw_min(vault, user):
    with brownie.reverts("amount < min"):
        vault.withdraw(1, 1000, {"from": user})


@given(
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 128),
    shares=strategy("uint256", min_value=1),
    user=strategy("address", exclude=ZERO_ADDRESS),
)
def test_withdraw_no_loss(chain, vault, token, uToken, user, deposit_amount, shares):
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    chain.mine(vault.blockDelay())

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
            "vault": {
                "totalAssets": vault.totalAssets(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    _shares = min(shares, uToken.balanceOf(user))
    calc = vault.calcWithdraw(_shares)

    before = snapshot()
    tx = vault.withdraw(_shares, calc, {"from": user})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [user, _shares, calc]

    diff = after["token"]["user"] - before["token"]["user"]
    assert diff == calc
    assert after["token"]["user"] == before["token"]["user"] + diff
    assert after["token"]["vault"] == before["token"]["vault"] - diff

    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
    assert after["vault"]["balanceOfVault"] == after["token"]["vault"]
    assert after["vault"]["debt"] == before["vault"]["debt"]

    assert after["uToken"]["user"] == before["uToken"]["user"] - _shares
    assert after["uToken"]["totalSupply"] == before["uToken"]["totalSupply"] - _shares
