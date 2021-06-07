import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, timeLock, testFundManager, user):
    if vault.fundManager() != testFundManager.address:
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
    token.mint(testFundManager, gain)

    before = snapshot()
    tx = vault.report(gain, 0, {"from": testFundManager})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"]
    assert after["token"]["fundManager"] == before["token"]["fundManager"]
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["debt"] == before["vault"]["debt"] + gain
    assert after["vault"]["lockedProfit"] > before["vault"]["lockedProfit"]

    assert vault.lastReport() == tx.timestamp

    assert tx.events["Report"].values() == [
        testFundManager.address,
        vault.debt(),
        gain,
        0,
        vault.lockedProfit(),
    ]

    # test loss
    if loss > vault.debt():
        with brownie.reverts("Integer underflow"):
            vault.report(0, loss, {"from": testFundManager})
        return

    before = snapshot()
    tx = vault.report(0, loss, {"from": testFundManager})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"]
    assert after["token"]["fundManager"] == before["token"]["fundManager"]
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["debt"] == before["vault"]["debt"] - loss
    if before["vault"]["lockedProfit"] > loss:
        assert after["vault"]["lockedProfit"] == before["vault"]["lockedProfit"] - loss
    else:
        assert after["vault"]["lockedProfit"] == 0

    assert vault.lastReport() == tx.timestamp

    assert tx.events["Report"].values() == [
        testFundManager.address,
        vault.debt(),
        0,
        loss,
        vault.lockedProfit(),
    ]


def test_report_not_fund_manager(vault, user):
    with brownie.reverts("!fund manager"):
        vault.report(0, 0, {"from": user})


def test_report_non_zero_gain_and_loss(vault, testFundManager):
    with brownie.reverts("gain and loss > 0"):
        vault.report(1, 1, {"from": testFundManager})


def test_report_balance_less_than_gain(vault, testFundManager):
    with brownie.reverts("gain < bal"):
        vault.report(1, 0, {"from": testFundManager})