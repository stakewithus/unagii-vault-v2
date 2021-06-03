import brownie
import pytest


def test_set_guardian(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setGuardian(user, {"from": user})

    # new guardian is current guardian
    with brownie.reverts("new guardian = current"):
        vault.setGuardian(vault.guardian(), {"from": admin})

    tx = vault.setGuardian(user, {"from": admin})
    assert vault.guardian() == user
    assert len(tx.events) == 1
    assert tx.events["SetGuardian"].values() == [user]
