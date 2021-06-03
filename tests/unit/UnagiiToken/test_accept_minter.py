import brownie
import pytest


def test_accept_minter(uToken, minter, user):
    uToken.setNextMinter(user, {"from": minter})

    # not next minter
    with brownie.reverts("!next minter"):
        uToken.acceptMinter({"from": minter})

    tx = uToken.acceptMinter({"from": user})
    assert uToken.minter() == user
    assert len(tx.events) == 1
    assert tx.events["AcceptMinter"].values() == [user]
