import brownie
import pytest


def test_sweep(vault, token, TestToken, admin, user):
    timeLock = vault.timeLock()

    anotherToken = TestToken.deploy("test", "TEST", 18, {"from": admin})

    # not auth
    with brownie.reverts("!auth"):
        vault.sweep(token, {"from": user})

    # protected token
    with brownie.reverts("protected"):
        vault.sweep(token, {"from": admin})

    # time lock
    vault.sweep(anotherToken, {"from": timeLock})

    # admin
    vault.sweep(anotherToken, {"from": admin})