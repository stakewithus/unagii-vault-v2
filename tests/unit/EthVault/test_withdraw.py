import brownie
from brownie import ZERO_ADDRESS
from brownie import test
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, ethVault, admin, user):
    ethVault.deposit(100, 1, {"from": user, "value": 100})


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
def test_withdraw_no_loss(ethVault, uEth, user, deposit_amount, shares):
    vault = ethVault
    vault.deposit(deposit_amount, 1, {"from": user, "value": deposit_amount})

    def snapshot():
        return {
            "eth": {"vault": vault.balance(), "user": user.balance()},
            "uEth": {
                "user": uEth.balanceOf(user),
                "totalSupply": uEth.totalSupply(),
            },
            "vault": {
                "totalAssets": vault.totalAssets(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    _shares = min(shares, uEth.balanceOf(user))
    calc = vault.calcWithdraw(_shares)

    before = snapshot()
    tx = vault.withdraw(shares, 1, {"from": user})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [user, _shares, calc]

    diff = after["eth"]["user"] - before["eth"]["user"]
    assert diff == calc
    assert after["eth"]["user"] == before["eth"]["user"] + diff
    assert after["eth"]["vault"] == before["eth"]["vault"] - diff

    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
    assert after["vault"]["debt"] == before["vault"]["debt"]
    assert after["vault"]["balanceOfVault"] == after["eth"]["vault"]

    assert after["uEth"]["user"] == before["uEth"]["user"] - _shares
    assert after["uEth"]["totalSupply"] == before["uEth"]["totalSupply"] - _shares


@given(
    deposit_amount=strategy("uint256", min_value=1, max_value=1000),
    loss=strategy("uint256"),
    shares=strategy("uint256", min_value=1),
    user=strategy("address", exclude=ZERO_ADDRESS),
)
def test_withdraw_maybe_loss(
    ethVault, testEthFundManager, uEth, user, admin, deposit_amount, loss, shares
):
    vault = ethVault
    fundManager = testEthFundManager
    timeLock = vault.timeLock()

    vault.setFundManager(fundManager, {"from": timeLock})

    vault.deposit(deposit_amount, 1, {"from": user, "value": deposit_amount})

    vault.borrow(2 ** 256 - 1, {"from": fundManager})

    _shares = min(shares, uEth.balanceOf(user))
    calc = vault.calcWithdraw(_shares)
    bal = vault.balance()
    debt = vault.debt()
    fund_manager_bal = fundManager.balance()

    _loss = min(calc, debt, loss, fund_manager_bal)
    fundManager.setLoss(_loss)

    def snapshot():
        return {
            "eth": {"vault": vault.balance(), "user": user.balance()},
            "vault": {
                "totalAssets": vault.totalAssets(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    before = snapshot()
    vault.withdraw(_shares, 0, {"from": user})
    after = snapshot()

    diff = after["eth"]["user"] - before["eth"]["user"]

    # withdrew from fund manager
    if calc > bal:
        assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - calc

        # loss equal to fund manager bal
        if _loss >= fund_manager_bal:
            # some transferred from vault
            assert after["vault"]["balanceOfVault"] == before["vault"][
                "balanceOfVault"
            ] - (calc - _loss)
            # 0 transferred from fund manager
            assert after["vault"]["debt"] == before["vault"]["debt"] - _loss
        else:
            # all losses are paid from fund manager
            fund_manager_diff = min(calc - bal, fund_manager_bal - _loss)

            assert after["vault"]["balanceOfVault"] == before["vault"][
                "balanceOfVault"
            ] + fund_manager_diff - min(calc - _loss, bal + fund_manager_diff)

            assert (
                after["vault"]["debt"]
                == before["vault"]["debt"] - _loss - fund_manager_diff
            )
    else:
        assert diff == calc
        assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - diff
        assert (
            after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] - diff
        )
        assert after["vault"]["debt"] == before["vault"]["debt"]

    assert after["eth"]["vault"] == after["vault"]["balanceOfVault"]
