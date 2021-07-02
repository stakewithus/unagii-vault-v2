import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, ethVault, admin, testEthFundManager, user):
    if ethVault.fundManager() != testEthFundManager.address:
        timeLock = ethVault.timeLock()
        ethVault.setFundManager(testEthFundManager, {"from": timeLock})


@given(
    debt=strategy("uint256", min_value=1, max_value=1000),
    gain=strategy("uint256", min_value=1, max_value=1000),
    loss=strategy("uint256", min_value=1, max_value=2 ** 128 - 1),
)
def test_report(ethVault, testEthFundManager, user, debt, gain, loss):
    vault = ethVault
    fundManager = testEthFundManager

    # deposit into vault
    vault.deposit(debt, 1, {"from": user, "value": debt})

    # borrow
    vault.borrow(debt, {"from": fundManager})

    def snapshot():
        return {
            "eth": {"vault": vault.balance(), "fundManager": fundManager.balance()},
            "vault": {
                "lockedProfit": vault.lockedProfit(),
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
            },
        }

    # test gain
    user.transfer(fundManager, gain)

    before = snapshot()
    tx = vault.report(gain, 0, {"from": fundManager})
    after = snapshot()

    assert after["eth"]["vault"] == before["eth"]["vault"]
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"]
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["debt"] == before["vault"]["debt"] + gain
    assert after["vault"]["lockedProfit"] >= before["vault"]["lockedProfit"] + gain

    assert vault.lastReport() == tx.timestamp

    assert tx.events["Report"].values() == [
        fundManager.address,
        vault.debt(),
        gain,
        0,
        vault.lockedProfit(),
    ]

    # test loss
    if loss > vault.debt():
        with brownie.reverts("Integer underflow"):
            vault.report(0, loss, {"from": fundManager})
        return

    before = snapshot()
    tx = vault.report(0, loss, {"from": fundManager})
    after = snapshot()

    assert after["eth"]["vault"] == before["eth"]["vault"]
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"]
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["debt"] == before["vault"]["debt"] - loss
    if before["vault"]["lockedProfit"] > loss:
        assert after["vault"]["lockedProfit"] == before["vault"]["lockedProfit"] - loss
    else:
        assert after["vault"]["lockedProfit"] == 0

    assert vault.lastReport() == tx.timestamp

    assert tx.events["Report"].values() == [
        fundManager.address,
        vault.debt(),
        0,
        loss,
        vault.lockedProfit(),
    ]


def test_report_not_fund_manager(ethVault, user):
    with brownie.reverts("!fund manager"):
        ethVault.report(0, 0, {"from": user})


def test_report_non_zero_gain_and_loss(ethVault, testEthFundManager):
    with brownie.reverts("gain and loss > 0"):
        ethVault.report(1, 1, {"from": testEthFundManager})


def test_report_balance_less_than_gain(ethVault, testEthFundManager):
    with brownie.reverts("gain < bal"):
        ethVault.report(1, 0, {"from": testEthFundManager})