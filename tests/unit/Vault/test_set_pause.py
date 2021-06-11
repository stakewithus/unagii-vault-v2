import brownie
import pytest


def test_set_pause(vault, admin, guardian, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setPause(True, {"from": user})

    # time lock can pause
    tx = vault.setPause(True, {"from": timeLock})
    assert vault.paused()
    assert tx.events["SetPause"].values() == [True]

    # admin can pause
    tx = vault.setPause(False, {"from": admin})
    assert not vault.paused()

    # guardian can pause
    vault.setPause(True, {"from": guardian})
    assert vault.paused()
