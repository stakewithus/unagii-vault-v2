import brownie
import pytest


def test_set_locked_profit_degradation(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setLockedProfitDegradation(123, {"from": user})

    # over max
    with brownie.reverts("degradation > max"):
        vault.setLockedProfitDegradation(10 ** 18 + 1, {"from": admin})

    # admin can call
    vault.setLockedProfitDegradation(123, {"from": admin})
    assert vault.lockedProfitDegradation() == 123
