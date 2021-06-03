import brownie
import pytest


def test_set_white_list(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setWhitelist(user, True, {"from": user})

    # admin can call
    vault.setWhitelist(user, True, {"from": admin})
    assert vault.whitelist(user)
