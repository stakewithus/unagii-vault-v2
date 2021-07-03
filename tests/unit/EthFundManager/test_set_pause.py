import brownie
import pytest


def test_set_pause(ethFundManager, admin, guardian, user):
    fundManager = ethFundManager

    # not admin
    with brownie.reverts("!auth"):
        fundManager.setPause(True, {"from": user})

    timeLock = fundManager.timeLock()

    # time lock can pause
    tx = fundManager.setPause(True, {"from": timeLock})
    assert fundManager.paused()
    assert tx.events["SetPause"].values() == [True]

    # admin can pause
    fundManager.setPause(False, {"from": admin})
    assert not fundManager.paused()

    # guardian can pause
    fundManager.setPause(True, {"from": guardian})
    assert fundManager.paused()
