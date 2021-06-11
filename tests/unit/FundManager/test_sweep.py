import brownie
import pytest


def test_sweep(fundManager, token, TestToken, admin, user):
    timeLock = fundManager.timeLock()
    anotherToken = TestToken.deploy("test", "TEST", 18, {"from": admin})

    # not auth
    with brownie.reverts("!auth"):
        fundManager.sweep(token, {"from": user})

    # protected token
    with brownie.reverts("protected"):
        fundManager.sweep(token, {"from": admin})

    # time lock
    fundManager.sweep(anotherToken, {"from": timeLock})

    # admin
    fundManager.sweep(anotherToken, {"from": admin})