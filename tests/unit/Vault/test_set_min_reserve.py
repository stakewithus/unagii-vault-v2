import brownie
import pytest


def test_set_min_reserve(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setMinReserve(123, {"from": user})

    # over max
    with brownie.reverts("min reserve > max"):
        vault.setMinReserve(10001, {"from": admin})

    # admin can call
    vault.setMinReserve(123, {"from": admin})
    assert vault.minReserve() == 123
