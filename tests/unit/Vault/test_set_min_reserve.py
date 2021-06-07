import brownie
import pytest


def test_set_min_reserve(vault, admin, keeper, user):
    # not auth
    with brownie.reverts("!auth"):
        vault.setMinReserve(123, {"from": user})

    # over max
    with brownie.reverts("min reserve > max"):
        vault.setMinReserve(10001, {"from": admin})

    # admin
    vault.setMinReserve(123, {"from": admin})
    assert vault.minReserve() == 123

    # keeper
    vault.setMinReserve(321, {"from": keeper})
    assert vault.minReserve() == 321