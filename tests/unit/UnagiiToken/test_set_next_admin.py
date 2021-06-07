import brownie
import pytest


def test_set_next_admin(uToken, user):
    admin = uToken.admin()

    # not admin
    with brownie.reverts("!admin"):
        uToken.setNextAdmin(user, {"from": user})

    tx = uToken.setNextAdmin(user, {"from": admin})
    assert uToken.nextAdmin() == user
    assert len(tx.events) == 1
    assert tx.events["SetNextAdmin"].values() == [user]
