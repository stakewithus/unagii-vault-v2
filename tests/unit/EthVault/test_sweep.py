import brownie
import pytest


def test_sweep(ethVault, TestToken, admin, user):
    timeLock = ethVault.timeLock()

    anotherToken = TestToken.deploy("test", "TEST", 18, {"from": admin})

    # not auth
    with brownie.reverts("!auth"):
        ethVault.sweep(anotherToken, {"from": user})

    # time lock
    ethVault.sweep(anotherToken, {"from": timeLock})

    # admin
    ethVault.sweep(anotherToken, {"from": admin})