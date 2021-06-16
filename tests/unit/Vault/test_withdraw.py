import brownie
from brownie import ZERO_ADDRESS
from brownie import test
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
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 128),
    shares=strategy("uint256", min_value=1),
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
            "vault": {
                "totalAssets": vault.totalAssets(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    _shares = min(shares, uToken.balanceOf(user))
    calc = vault.calcWithdraw(_shares)

    before = snapshot()
    vault.withdraw(shares, 1, {"from": user})
    after = snapshot()

    diff = after["token"]["user"] - before["token"]["user"]
    assert diff == calc
    assert after["token"]["vault"] == before["token"]["vault"] - diff

    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
    assert after["vault"]["debt"] == before["vault"]["debt"]
    assert after["vault"]["balanceOfVault"] == after["token"]["vault"]

    assert after["uToken"]["user"] == before["uToken"]["user"] - _shares
    assert after["uToken"]["totalSupply"] == before["uToken"]["totalSupply"] - _shares


@given(
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 128),
    loss=strategy("uint256"),
    shares=strategy("uint256", min_value=1),
    user=strategy("address", exclude=ZERO_ADDRESS),
)
def test_withdraw_from_fund_manager(
    vault, testFundManager, token, uToken, user, admin, deposit_amount, loss, shares
):
    fundManager = testFundManager
    timeLock = vault.timeLock()

    vault.setFundManager(fundManager, {"from": timeLock})

    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    vault.borrow(2 ** 256 - 1, {"from": fundManager})

    fundManager.setLoss(2 ** 256 - 1)

    calc = vault.calcWithdraw(uToken.balanceOf(user))
    bal = vault.balanceOfVault()
    if calc > bal:
        with brownie.reverts("loss + diff > need"):
            vault.withdraw(2 ** 256 - 1, 0, {"from": user})

    _shares = min(shares, uToken.balanceOf(user))
    calc = vault.calcWithdraw(_shares)
    bal = token.balanceOf(vault)

    _loss = 0
    if calc > bal:
        # max loss from fund manager
        _loss = calc - bal
    _loss = min(_loss, loss)

    fundManager.setLoss(_loss)

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "user": token.balanceOf(user),
            },
            "vault": {
                "totalAssets": vault.totalAssets(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    before = snapshot()
    vault.withdraw(_shares, 0, {"from": user})
    after = snapshot()

    diff = after["token"]["user"] - before["token"]["user"]

    assert after["token"]["vault"] == after["vault"]["balanceOfVault"]

    if calc >= bal:
        assert diff + _loss == calc
        assert (
            after["vault"]["totalAssets"]
            == before["vault"]["totalAssets"] - diff - _loss
        )
        assert after["vault"]["balanceOfVault"] == 0
        after["vault"]["debt"] == before["vault"]["debt"] - (calc - bal)
    else:
        assert diff == calc
        assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
        assert (
            after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
        )
        assert after["vault"]["debt"] == before["vault"]["debt"]
