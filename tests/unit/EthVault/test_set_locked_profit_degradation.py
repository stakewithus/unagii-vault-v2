import brownie
import pytest


def test_set_locked_profit_degradation(ethVault, admin, user):
    vault = ethVault
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setLockedProfitDegradation(123, {"from": user})

    # over max
    with brownie.reverts("degradation > max"):
        vault.setLockedProfitDegradation(10 ** 18 + 1, {"from": admin})

    # time lock can call
    vault.setLockedProfitDegradation(123, {"from": timeLock})
    assert vault.lockedProfitDegradation() == 123

    # admin can call
    vault.setLockedProfitDegradation(321, {"from": admin})
    assert vault.lockedProfitDegradation() == 321
