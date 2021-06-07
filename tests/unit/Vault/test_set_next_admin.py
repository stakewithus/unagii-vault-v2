import brownie
import pytest


def test_set_next_admin(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setNextAdmin(user, {"from": user})

    tx = vault.setNextAdmin(user, {"from": admin})
    assert vault.nextAdmin() == user
    assert len(tx.events) == 1
    assert tx.events["SetNextAdmin"].values() == [user]
