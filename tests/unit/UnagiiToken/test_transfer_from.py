import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@given(
    accs=strategy(
        "address[]", min_length=3, max_length=3, unique=True, exclude=ZERO_ADDRESS
    ),
    mint_amount=strategy("uint256"),
    transfer_amount=strategy("uint256"),
    approve_amount=strategy("uint256", exclude=2 * 256 - 1),
)
def test_transfer_from(
    uToken, minter, accs, mint_amount, transfer_amount, approve_amount
):
    caller = accs[0]
    owner = accs[1]
    receiver = accs[2]
    uToken.mint(owner, mint_amount, {"from": minter})
    uToken.approve(caller, approve_amount, {"from": owner})

    bal = uToken.balanceOf(owner)
    # transfer > allowance
    # transfer > balance
    if transfer_amount > approve_amount or transfer_amount > bal:
        with brownie.reverts():
            uToken.transferFrom(owner, receiver, transfer_amount, {"from": caller})
        return

    # transfer <= allowance and balance
    def snapshot():
        return {
            "balance": {
                "caller": uToken.balanceOf(caller),
                "owner": uToken.balanceOf(owner),
                "receiver": uToken.balanceOf(receiver),
            },
            "allowance": {
                "caller": uToken.allowance(owner, caller),
                "owner": uToken.allowance(owner, owner),
                "receiver": uToken.allowance(owner, receiver),
            },
            "totalSupply": uToken.totalSupply(),
        }

    before = snapshot()
    tx = uToken.transferFrom(owner, receiver, transfer_amount, {"from": caller})
    after = snapshot()

    assert after["balance"]["caller"] == before["balance"]["caller"]
    assert after["balance"]["owner"] == before["balance"]["owner"] - transfer_amount
    assert (
        after["balance"]["receiver"] == before["balance"]["receiver"] + transfer_amount
    )
    assert (
        after["allowance"]["caller"] == before["allowance"]["caller"] - transfer_amount
    )
    assert after["allowance"]["owner"] == before["allowance"]["owner"]
    assert after["allowance"]["receiver"] == before["allowance"]["receiver"]
    assert uToken.lastBlock(owner) == tx.block_number
    assert uToken.lastBlock(receiver) == tx.block_number
    assert after["totalSupply"] == before["totalSupply"]


def test_transfer_from_to_owner(uToken, minter, accounts):
    caller = accounts[0]
    owner = accounts[1]
    amount = 123
    uToken.mint(owner, amount, {"from": minter})
    uToken.approve(caller, amount, {"from": owner})

    bal = uToken.balanceOf(owner)
    uToken.transferFrom(owner, owner, amount, {"from": caller})

    assert uToken.balanceOf(owner) == bal


def test_transfer_from_infinite_approval(uToken, minter, accounts):
    caller = accounts[0]
    owner = accounts[1]
    receiver = accounts[2]
    amount = 123
    uToken.mint(owner, amount, {"from": minter})
    uToken.approve(caller, 2 ** 256 - 1, {"from": owner})

    uToken.transferFrom(owner, receiver, amount, {"from": caller})

    assert uToken.allowance(owner, caller) == 2 ** 256 - 1


def test_transfer_from_to_self(uToken, accounts):
    caller = accounts[0]
    owner = accounts[1]
    receiver = uToken.address
    uToken.approve(caller, 1, {"from": owner})

    with brownie.reverts("invalid receiver"):
        uToken.transferFrom(owner, receiver, 1, {"from": caller})


def test_transfer_from_to_zero_address(uToken, accounts):
    caller = accounts[0]
    owner = accounts[1]
    receiver = ZERO_ADDRESS
    uToken.approve(caller, 1, {"from": owner})

    with brownie.reverts("invalid receiver"):
        uToken.transferFrom(owner, receiver, 1, {"from": caller})
