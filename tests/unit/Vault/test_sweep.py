import brownie
import pytest


def test_sweep(vault, token, TestToken, admin, user):
    anotherToken = TestToken.deploy("test", "TEST", 18, {"from": admin})

    # not admin
    with brownie.reverts("!admin"):
        vault.sweep(token, {"from": user})

    # protected token
    with brownie.reverts("protected"):
        vault.sweep(token, {"from": admin})

    vault.sweep(anotherToken, {"from": admin})
