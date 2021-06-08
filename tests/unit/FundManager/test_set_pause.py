import brownie
import pytest


def test_set_pause(fundManager, admin, guardian, keeper, user):
    # not admin
    with brownie.reverts("!auth"):
        fundManager.setPause(True, {"from": user})

    # admin can pause
    tx = fundManager.setPause(True, {"from": admin})
    assert fundManager.paused()
    assert len(tx.events) == 1
    assert tx.events["SetPause"].values() == [True]

    # guardian can pause
    tx = fundManager.setPause(False, {"from": guardian})
    assert not fundManager.paused()

    # keeper can pause
    tx = fundManager.setPause(True, {"from": keeper})
    assert fundManager.paused()
