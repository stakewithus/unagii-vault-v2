import brownie
import pytest


def test_set_time_lock(vault, timeLock, user):
    # not time lock
    with brownie.reverts("!time lock"):
        vault.setTimeLock(user, {"from": user})

    # new time lock is current time lock
    with brownie.reverts("new time lock = current"):
        vault.setTimeLock(timeLock, {"from": timeLock})

    vault.setTimeLock(user, {"from": timeLock})
    assert vault.timeLock() == user
