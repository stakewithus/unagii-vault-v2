import brownie
import pytest


def test_set_minter(uToken, minter, user):
    # not minter
    with brownie.reverts("!time lock"):
        uToken.setMinter(user, {"from": user})

    timeLock = uToken.timeLock()

    tx = uToken.setMinter(user, {"from": timeLock})
    assert uToken.minter() == user
    assert tx.events["SetMinter"].values() == [user]