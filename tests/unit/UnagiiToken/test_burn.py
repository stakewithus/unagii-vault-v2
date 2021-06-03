import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


@given(
    to=strategy("address", exclude=ZERO_ADDRESS),
    mint_amount=strategy("uint256"),
    burn_amount=strategy("uint256"),
)
def test_burn(uToken, minter, to, mint_amount, burn_amount):
    uToken.mint(to, mint_amount, {"from": minter})

    if burn_amount > mint_amount:
        with brownie.reverts():
            uToken.burn(to, burn_amount, {"from": minter})
        return

    totalSupply = uToken.totalSupply()
    bal = uToken.balanceOf(to)

    tx = uToken.burn(to, burn_amount, {"from": minter})

    assert uToken.balanceOf(to) == bal - burn_amount
    assert uToken.totalSupply() == totalSupply - burn_amount
    assert uToken.lastBlock(to) == tx.block_number


def test_burn_not_minter(uToken, minter, accounts):
    uToken.mint(accounts[1], 1, {"from": minter})

    with brownie.reverts("!minter"):
        uToken.burn(accounts[1], 1, {"from": accounts[1]})


def test_burn_zero_address(uToken, minter):
    with brownie.reverts("from = 0"):
        uToken.burn(ZERO_ADDRESS, 1, {"from": minter})