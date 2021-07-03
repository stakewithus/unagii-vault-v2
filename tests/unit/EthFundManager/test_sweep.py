import brownie
import pytest


def test_sweep(ethFundManager, TestToken, admin, user):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()
    anotherToken = TestToken.deploy("test", "TEST", 18, {"from": admin})

    # not auth
    with brownie.reverts("!auth"):
        fundManager.sweep(anotherToken, {"from": user})

    # time lock
    fundManager.sweep(anotherToken, {"from": timeLock})

    # admin
    fundManager.sweep(anotherToken, {"from": admin})