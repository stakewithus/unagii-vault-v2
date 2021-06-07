import brownie
import pytest


def test_set_minter(uToken, admin, minter, user):
    # not minter
    with brownie.reverts("!admin"):
        uToken.setMinter(user, {"from": user})

    # next minter is current minter
    with brownie.reverts("minter = current"):
        uToken.setMinter(minter, {"from": admin})

    tx = uToken.setMinter(user, {"from": admin})
    assert uToken.minter() == user
    assert len(tx.events) == 1
    assert tx.events["SetMinter"].values() == [user]