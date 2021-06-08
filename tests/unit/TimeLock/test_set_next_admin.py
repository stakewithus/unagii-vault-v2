import brownie
import pytest


def test_set_next_admin(timeLock, user):
    admin = timeLock.admin()

    # not admin
    with brownie.reverts("!admin"):
        timeLock.setNextAdmin(user, {"from": user})

    tx = timeLock.setNextAdmin(user, {"from": admin})
    assert timeLock.nextAdmin() == user
    assert len(tx.events) == 1
    assert tx.events["SetNextAdmin"].values() == [user]
