import brownie
import pytest


def test_accept_admin(uToken, user):
    admin = uToken.admin()
    uToken.setNextAdmin(user, {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        uToken.acceptAdmin({"from": admin})

    tx = uToken.acceptAdmin({"from": user})
    assert uToken.admin() == user
    assert len(tx.events) == 1
    assert tx.events["AcceptAdmin"].values() == [user]