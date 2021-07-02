import brownie
import pytest


def test_set_min_reserve(ethVault, admin, user):
    timeLock = ethVault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        ethVault.setMinReserve(123, {"from": user})

    # over max
    with brownie.reverts("min reserve > max"):
        ethVault.setMinReserve(10001, {"from": admin})

    # time lock
    ethVault.setMinReserve(123, {"from": timeLock})
    assert ethVault.minReserve() == 123

    # admin
    ethVault.setMinReserve(321, {"from": admin})
    assert ethVault.minReserve() == 321