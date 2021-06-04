import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


@given(
    to=strategy("address"),
    amount=strategy("uint256"),
)
def test_mint(uToken, minter, to, amount):
    if to in [uToken.address, ZERO_ADDRESS]:
        with brownie.reverts("invalid receiver"):
            uToken.mint(to, 1, {"from": minter})
        return

    totalSupply = uToken.totalSupply()
    bal = uToken.balanceOf(to)
    tx = uToken.mint(to, amount, {"from": minter})

    assert uToken.balanceOf(to) == bal + amount
    assert uToken.totalSupply() == totalSupply + amount
    assert uToken.lastBlock(to) == tx.block_number
    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [ZERO_ADDRESS, to, amount]


def test_mint_not_minter(uToken, accounts):
    with brownie.reverts("!minter"):
        uToken.mint(accounts[1], 1, {"from": accounts[1]})
