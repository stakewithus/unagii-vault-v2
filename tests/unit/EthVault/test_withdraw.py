import brownie
from brownie import ZERO_ADDRESS
from brownie import test
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, chain, ethVault, user):
    ethVault.deposit(1, {"from": user, "value": 1000})
    chain.mine(ethVault.blockDelay())


def test_withdraw_zero_shares(ethVault, user):
    with brownie.reverts("shares = 0"):
        ethVault.withdraw(0, 0, {"from": user})


def test_withdraw_min(ethVault, user):
    with brownie.reverts("amount < min"):
        ethVault.withdraw(1, 1000, {"from": user})


@given(
    deposit_amount=strategy("uint256", min_value=1, max_value=1000),
    shares=strategy("uint256", min_value=1),
    user=strategy("address", exclude=ZERO_ADDRESS),
)
def test_withdraw_no_loss(chain, ethVault, uEth, user, deposit_amount, shares):
    vault = ethVault
    vault.deposit(1, {"from": user, "value": deposit_amount})

    chain.mine(vault.blockDelay())

    def snapshot():
        return {
            "eth": {"vault": vault.balance(), "user": user.balance()},
            "uEth": {
                "user": uEth.balanceOf(user),
                "totalSupply": uEth.totalSupply(),
            },
            "vault": {
                "totalAssets": vault.totalAssets(),
                "totalDebt": vault.totalDebt(),
            },
        }

    _shares = min(shares, uEth.balanceOf(user))
    calc = vault.calcWithdraw(_shares)

    before = snapshot()
    tx = vault.withdraw(_shares, calc, {"from": user})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [user, _shares, calc]

    diff = after["eth"]["user"] - before["eth"]["user"]
    assert diff == calc
    assert after["eth"]["user"] == before["eth"]["user"] + diff
    assert after["eth"]["vault"] == before["eth"]["vault"] - diff

    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
    assert after["vault"]["totalDebt"] == before["vault"]["totalDebt"]

    assert after["uEth"]["user"] == before["uEth"]["user"] - _shares
    assert after["uEth"]["totalSupply"] == before["uEth"]["totalSupply"] - _shares
