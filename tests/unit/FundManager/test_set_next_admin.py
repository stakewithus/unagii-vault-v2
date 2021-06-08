import brownie
import pytest


def test_set_next_admin(fundManager, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        fundManager.setNextAdmin(user, {"from": user})

    tx = fundManager.setNextAdmin(user, {"from": admin})
    assert fundManager.nextAdmin() == user
    assert len(tx.events) == 1
    assert tx.events["SetNextAdmin"].values() == [user]
