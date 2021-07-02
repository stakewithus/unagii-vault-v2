import brownie
import pytest


def test_set_pause(ethVault, admin, guardian, user):
    timeLock = ethVault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        ethVault.setPause(True, {"from": user})

    # time lock can pause
    tx = ethVault.setPause(True, {"from": timeLock})
    assert ethVault.paused()
    assert tx.events["SetPause"].values() == [True]

    # admin can pause
    tx = ethVault.setPause(False, {"from": admin})
    assert not ethVault.paused()

    # guardian can pause
    ethVault.setPause(True, {"from": guardian})
    assert ethVault.paused()
