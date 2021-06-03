import brownie
import pytest


def test_set_pause(vault, admin, guardian, user):
    # not admin
    with brownie.reverts("!auth"):
        vault.setPause(True, {"from": user})

    # guadian can pause
    tx = vault.setPause(False, {"from": guardian})
    assert not vault.paused()
    assert len(tx.events) == 1
    assert tx.events["SetPause"].values() == [False]

    # admin can pause
    tx = vault.setPause(True, {"from": admin})
    assert vault.paused()
    assert len(tx.events) == 1
    assert tx.events["SetPause"].values() == [True]
