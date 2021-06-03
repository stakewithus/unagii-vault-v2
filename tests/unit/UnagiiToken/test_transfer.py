import brownie
from brownie.test import given, strategy
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


@given(
    sender=strategy("address", exclude=ZERO_ADDRESS),
    receiver=strategy("address", exclude=ZERO_ADDRESS),
    mint_amount=strategy("uint256"),
    transfer_amount=strategy("uint256"),
)
def test_transfer(uToken, minter, sender, receiver, mint_amount, transfer_amount):
    if receiver == uToken.address:
        # skip
        return

    uToken.mint(sender, mint_amount, {"from": minter})

    bal = uToken.balanceOf(sender)
    # test transfer more than balance
    if bal < transfer_amount:
        with brownie.reverts():
            uToken.transfer(receiver, transfer_amount, {"from": sender})
        return

    def snapshot():
        return {
            "balance": {
                "sender": uToken.balanceOf(sender),
                "receiver": uToken.balanceOf(receiver),
            },
            "totalSupply": uToken.totalSupply(),
        }

    # test transfer less than or equal to balance
    before = snapshot()
    tx = uToken.transfer(receiver, transfer_amount, {"from": sender})
    after = snapshot()

    if sender == receiver:
        assert after["balance"]["sender"] == before["balance"]["sender"]
        assert after["balance"]["receiver"] == before["balance"]["receiver"]
    else:
        assert (
            after["balance"]["sender"] == before["balance"]["sender"] - transfer_amount
        )
        assert (
            after["balance"]["receiver"]
            == before["balance"]["receiver"] + transfer_amount
        )

    assert after["totalSupply"] == before["totalSupply"]
    assert uToken.lastBlock(sender) == tx.block_number
    assert uToken.lastBlock(receiver) == tx.block_number
    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [sender, receiver, transfer_amount]


def test_transfer_to_self(uToken, accounts):
    with brownie.reverts("invalid receiver"):
        uToken.transfer(uToken.address, 1, {"from": accounts[1]})


def test_transfer_to_zero_address(uToken, accounts):
    with brownie.reverts("invalid receiver"):
        uToken.transfer(ZERO_ADDRESS, 1, {"from": accounts[1]})
