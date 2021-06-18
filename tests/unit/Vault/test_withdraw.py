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
def test_withdraw_no_loss(vault, token, uToken, user, deposit_amount, shares):
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
    tx = vault.withdraw(shares, 1, {"from": user})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [user, _shares, calc]

    diff = after["token"]["user"] - before["token"]["user"]
    assert diff == calc
    assert after["token"]["user"] == before["token"]["user"] + diff
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
def test_withdraw_maybe_loss(
    vault, testFundManager, token, uToken, user, admin, deposit_amount, loss, shares
):
    fundManager = testFundManager
    timeLock = vault.timeLock()

    vault.setFundManager(fundManager, {"from": timeLock})

    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    vault.borrow(2 ** 256 - 1, {"from": fundManager})

    _shares = min(shares, uToken.balanceOf(user))
    calc = vault.calcWithdraw(_shares)
    bal = token.balanceOf(vault)
    debt = vault.debt()

    _loss = min(calc, debt, loss)
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

    # withdrew from fund manager
    if calc > bal:
        assert diff == calc - _loss
        assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - calc

        # loss is greater than or equal to amount to withdraw from fund manager
        if _loss >= calc - bal:
            # some transferred from vault
            assert (
                after["vault"]["balanceOfVault"]
                == before["vault"]["balanceOfVault"] - diff
            )
            # 0 transferred from fund manager
            assert after["vault"]["debt"] == before["vault"]["debt"] - _loss
        else:
            # all losses are paid from fund manager
            # all transferred from vault
            assert (
                after["vault"]["balanceOfVault"]
                == before["vault"]["balanceOfVault"] - bal
            )
            assert after["vault"]["debt"] == before["vault"]["debt"] - (calc - bal)
    else:
        assert diff == calc
        assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
        assert (
            after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
        )
        assert after["vault"]["debt"] == before["vault"]["debt"]

    assert after["token"]["vault"] == after["vault"]["balanceOfVault"]
