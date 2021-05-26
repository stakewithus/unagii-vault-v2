import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def snapshot(uToken, sender, receiver):
    return {
        "balance": {
            "sender": uToken.balanceOf(sender),
            "receiver": uToken.balanceOf(receiver),
        },
        "totalSupply": uToken.totalSupply(),
    }


@given(
    accs=strategy(
        "address[]", min_length=2, max_length=2, unique=True, exclude=ZERO_ADDRESS
    ),
    mint_amount=strategy("uint256"),
    transfer_amount=strategy("uint256"),
)
def test_transfer(uToken, minter, accs, mint_amount, transfer_amount):
    sender = accs[0]
    receiver = accs[1]
    uToken.mint(sender, mint_amount, {"from": minter})

    bal = uToken.balanceOf(sender)
    # test transfer more than balance
    if bal < transfer_amount:
        with brownie.reverts():
            uToken.transfer(receiver, transfer_amount, {"from": sender})
        return

    # test transfer less than or equal to balance
    before = snapshot(uToken, sender, receiver)
    tx = uToken.transfer(receiver, transfer_amount, {"from": sender})
    after = snapshot(uToken, sender, receiver)

    assert after["balance"]["sender"] == before["balance"]["sender"] - transfer_amount
    assert (
        after["balance"]["receiver"] == before["balance"]["receiver"] + transfer_amount
    )
    assert uToken.lastBlock(sender) == tx.block_number
    assert uToken.lastBlock(receiver) == tx.block_number
    assert after["totalSupply"] == before["totalSupply"]


def test_transfer_to_sender(uToken, minter, accounts):
    sender = accounts[0]
    amount = 123
    uToken.mint(sender, amount, {"from": minter})

    bal = uToken.balanceOf(sender)
    uToken.transfer(sender, amount, {"from": sender})

    assert uToken.balanceOf(sender) == bal


def test_transfer_to_self(uToken, minter, accounts):
    with brownie.reverts("invalid receiver"):
        uToken.transfer(uToken.address, 1, {"from": accounts[1]})


def test_transfer_to_zero_address(uToken, minter, accounts):
    with brownie.reverts("invalid receiver"):
        uToken.transfer(ZERO_ADDRESS, 1, {"from": accounts[1]})
