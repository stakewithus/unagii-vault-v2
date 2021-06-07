import brownie
import pytest


def test_set_locked_profit_degradation(vault, admin, keeper, user):
    # not auth
    with brownie.reverts("!auth"):
        vault.setLockedProfitDegradation(123, {"from": user})

    # over max
    with brownie.reverts("degradation > max"):
        vault.setLockedProfitDegradation(10 ** 18 + 1, {"from": admin})

    # admin
    vault.setLockedProfitDegradation(123, {"from": admin})
    assert vault.lockedProfitDegradation() == 123

    # keeper
    vault.setLockedProfitDegradation(321, {"from": keeper})
    assert vault.lockedProfitDegradation() == 321
