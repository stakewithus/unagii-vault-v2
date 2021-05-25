import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


@given(
    to=strategy("address", exclude=ZERO_ADDRESS),
    amount=strategy("uint256", max_value=10000),
)
def test_mint(uToken, minter, to, amount):
    total = uToken.totalSupply()
    bal = uToken.balanceOf(to)
    tx = uToken.mint(to, amount, {"from": minter})

    assert uToken.balanceOf(to) == bal + amount
    assert uToken.totalSupply() == total + amount
    assert uToken.lastBlock(to) == tx.block_number


def test_mint_not_minter(uToken, accounts):
    with brownie.reverts("!minter"):
        uToken.mint(accounts[1], 1, {"from": accounts[1]})


def test_mint_zero_address(uToken, minter):
    with brownie.reverts("receiver = 0 address"):
        uToken.mint(ZERO_ADDRESS, 1, {"from": minter})