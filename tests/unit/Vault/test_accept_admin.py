import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_accept_admin(vault, admin, user):
    vault.setNextAdmin(user, {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        vault.acceptAdmin({"from": admin})

    vault.acceptAdmin({"from": user})
    assert vault.admin() == user
    assert vault.nextAdmin() == ZERO_ADDRESS
