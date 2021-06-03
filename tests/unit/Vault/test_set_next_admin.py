import brownie
import pytest


def test_set_next_admin(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setNextAdmin(user, {"from": user})

    # next admin is current admin
    with brownie.reverts("next admin = current"):
        vault.setNextAdmin(admin, {"from": admin})

    vault.setNextAdmin(user, {"from": admin})
    assert vault.nextAdmin() == user
