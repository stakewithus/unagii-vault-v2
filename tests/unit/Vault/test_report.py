import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, admin, testFundManager, user):
    if vault.fundManager() != testFundManager.address:
        timeLock = vault.timeLock()
        vault.setFundManager(testFundManager, {"from": timeLock})


@given(
    debt=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    gain=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
    loss=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
)
def test_report(vault, token, testFundManager, user, debt, gain, loss):
    fundManager = testFundManager

    # deposit into vault
    token.mint(user, debt)
    token.approve(vault, debt, {"from": user})
    vault.deposit(debt, 1, {"from": user})

    # borrow
    vault.borrow(debt, {"from": testFundManager})

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "fundManager": token.balanceOf(fundManager),
            },
            "vault": {
                "lockedProfit": vault.lockedProfit(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    # test gain
    token.mint(fundManager, gain)
    token.approve(vault, gain, {"from": fundManager})

    before = snapshot()
    tx = vault.report(gain, 0, {"from": fundManager})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"] + gain
    assert after["token"]["fundManager"] == before["token"]["fundManager"] - gain
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"] + gain
    assert after["vault"]["debt"] == before["vault"]["debt"]
    assert after["vault"]["lockedProfit"] >= before["vault"]["lockedProfit"] + gain

    assert vault.lastReport() == tx.timestamp

    assert tx.events["Report"].values() == [
        fundManager.address,
        vault.balanceOfVault(),
        vault.debt(),
        gain,
        0,
        gain,
        vault.lockedProfit(),
    ]

    # test loss
    _loss = min(loss, vault.debt())

    before = snapshot()
    tx = vault.report(0, _loss, {"from": fundManager})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"]
    assert after["token"]["fundManager"] == before["token"]["fundManager"]
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["debt"] == before["vault"]["debt"] - _loss
    if before["vault"]["lockedProfit"] > _loss:
        assert after["vault"]["lockedProfit"] == before["vault"]["lockedProfit"] - _loss
    else:
        assert after["vault"]["lockedProfit"] == 0

    assert vault.lastReport() == tx.timestamp

    assert tx.events["Report"].values() == [
        fundManager.address,
        vault.balanceOfVault(),
        vault.debt(),
        0,
        _loss,
        0,
        vault.lockedProfit(),
    ]


def test_report_not_fund_manager(vault, user):
    with brownie.reverts("!fund manager"):
        vault.report(0, 0, {"from": user})


def test_report_non_zero_gain_and_loss(vault, testFundManager):
    with brownie.reverts("gain and loss > 0"):
        vault.report(1, 1, {"from": testFundManager})
