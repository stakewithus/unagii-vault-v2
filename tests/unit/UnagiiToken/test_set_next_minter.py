import brownie
import pytest


def test_set_next_minter(uToken, minter, user):
    # not minter
    with brownie.reverts("!minter"):
        uToken.setNextMinter(user, {"from": user})

    # next minter is current minter
    with brownie.reverts("next minter = current"):
        uToken.setNextMinter(minter, {"from": minter})

    tx = uToken.setNextMinter(user, {"from": minter})
    assert uToken.nextMinter() == user
    assert len(tx.events) == 1
    assert tx.events["SetNextMinter"].values() == [user]