import brownie
import pytest


def test_set_locked_profit_degradation(ethVault, admin, user):
    timeLock = ethVault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        ethVault.setLockedProfitDegradation(123, {"from": user})

    # over max
    with brownie.reverts("degradation > max"):
        ethVault.setLockedProfitDegradation(10 ** 18 + 1, {"from": admin})

    # time lock
    ethVault.setLockedProfitDegradation(123, {"from": timeLock})
    assert ethVault.lockedProfitDegradation() == 123

    # admin
    ethVault.setLockedProfitDegradation(321, {"from": admin})
    assert ethVault.lockedProfitDegradation() == 321
