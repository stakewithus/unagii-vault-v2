import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_accept_admin(timeLock, admin, user):
    timeLock.setNextAdmin(user, {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        timeLock.acceptAdmin({"from": admin})

    tx = timeLock.acceptAdmin({"from": user})
    assert timeLock.admin() == user
    assert timeLock.nextAdmin() == ZERO_ADDRESS
    assert len(tx.events) == 1
    assert tx.events["AcceptAdmin"].values() == [user]