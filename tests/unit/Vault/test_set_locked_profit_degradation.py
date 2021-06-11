import brownie
import pytest


def test_set_locked_profit_degradation(vault, admin, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setLockedProfitDegradation(123, {"from": user})

    # over max
    with brownie.reverts("degradation > max"):
        vault.setLockedProfitDegradation(10 ** 18 + 1, {"from": admin})

    # time lock
    vault.setLockedProfitDegradation(123, {"from": timeLock})
    assert vault.lockedProfitDegradation() == 123

    # admin
    vault.setLockedProfitDegradation(321, {"from": admin})
    assert vault.lockedProfitDegradation() == 321
