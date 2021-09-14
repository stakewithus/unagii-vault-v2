import brownie
import pytest


def test_set_min_reserve(ethVault, admin, user):
    vault = ethVault
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setMinReserve(123, {"from": user})

    # over max
    with brownie.reverts("min reserve > max"):
        vault.setMinReserve(10001, {"from": admin})

    # time lock can call
    vault.setMinReserve(123, {"from": timeLock})
    assert vault.minReserve() == 123

    # admin can call
    vault.setMinReserve(321, {"from": admin})
    assert vault.minReserve() == 321