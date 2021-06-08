import brownie
import pytest


def test_accept_admin(fundManager, admin, user):
    fundManager.setNextAdmin(user, {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        fundManager.acceptAdmin({"from": admin})

    tx = fundManager.acceptAdmin({"from": user})
    assert fundManager.admin() == user
    assert len(tx.events) == 1
    assert tx.events["AcceptAdmin"].values() == [user]