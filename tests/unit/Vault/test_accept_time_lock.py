import brownie
import pytest


def test_accept_time_lock(vault, admin, timeLock, user):
    vault.setNextTimeLock(user, {"from": timeLock})

    # not next admin
    with brownie.reverts("!next time lock"):
        vault.acceptTimeLock({"from": timeLock})

    tx = vault.acceptTimeLock({"from": user})
    assert vault.timeLock() == user
    assert len(tx.events) == 1
    assert tx.events["AcceptTimeLock"].values() == [user]
