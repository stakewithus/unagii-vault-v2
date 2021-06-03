import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


@given(
    owner=strategy("address"),
    spender=strategy("address"),
    amount=strategy("uint256"),
)
def test_apprpve(uToken, owner, spender, amount):
    tx = uToken.approve(spender, amount, {"from": owner})
    assert uToken.allowance(owner, spender) == amount
    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [owner, spender, amount]


def test_increase_allowance(uToken, accounts):
    owner = accounts[0]
    spender = accounts[1]
    uToken.approve(spender, 100, {"from": owner})
    tx = uToken.increaseAllowance(spender, 403, {"from": owner})

    assert uToken.allowance(owner, spender) == 503
    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [owner, spender, 503]


def test_decrease_allowance(uToken, accounts):
    owner = accounts[0]
    spender = accounts[1]
    uToken.approve(spender, 100, {"from": owner})
    tx = uToken.decreaseAllowance(spender, 34, {"from": owner})

    assert uToken.allowance(owner, spender) == 66
    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [owner, spender, 66]
