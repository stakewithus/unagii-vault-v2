import brownie
import pytest


def test_accept_time_lock(vault, user):
    timeLock = vault.timeLock()

    vault.setNextTimeLock(user, {"from": timeLock})

    # not next time lock
    with brownie.reverts("!next time lock"):
        vault.acceptTimeLock({"from": timeLock})

    tx = vault.acceptTimeLock({"from": user})
    assert vault.timeLock() == user
    assert tx.events["AcceptTimeLock"].values() == [user]