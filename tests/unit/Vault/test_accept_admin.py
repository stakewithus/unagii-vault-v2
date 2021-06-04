import brownie
import pytest


def test_accept_admin(vault, admin, user):
    vault.setNextAdmin(user, {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        vault.acceptAdmin({"from": admin})

    tx = vault.acceptAdmin({"from": user})
    assert vault.admin() == user
    assert len(tx.events) == 1
    assert tx.events["AcceptAdmin"].values() == [user]