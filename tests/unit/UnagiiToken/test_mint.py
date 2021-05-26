import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


@given(
    to=strategy("address", exclude=ZERO_ADDRESS),
    amount=strategy("uint256"),
)
def test_mint(uToken, minter, to, amount):
    totalSupply = uToken.totalSupply()
    bal = uToken.balanceOf(to)
    tx = uToken.mint(to, amount, {"from": minter})

    assert uToken.balanceOf(to) == bal + amount
    assert uToken.totalSupply() == totalSupply + amount
    assert uToken.lastBlock(to) == tx.block_number


def test_mint_not_minter(uToken, accounts):
    with brownie.reverts("!minter"):
        uToken.mint(accounts[1], 1, {"from": accounts[1]})


def test_mint_zero_address(uToken, minter):
    with brownie.reverts("to = 0 address"):
        uToken.mint(ZERO_ADDRESS, 1, {"from": minter})