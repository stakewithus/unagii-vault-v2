import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_accept_time_lock(ethVault, user):
    vault = ethVault
    timeLock = vault.timeLock()

    vault.setNextTimeLock(user, {"from": timeLock})

    # not next time lock
    with brownie.reverts("!next time lock"):
        vault.acceptTimeLock({"from": timeLock})

    tx = vault.acceptTimeLock({"from": user})
    assert vault.timeLock() == user
    assert vault.nextTimeLock() == ZERO_ADDRESS
    assert tx.events["AcceptTimeLock"].values() == [user]