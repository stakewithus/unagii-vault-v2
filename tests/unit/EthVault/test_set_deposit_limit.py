import brownie
import pytest


def test_set_deposit_limit(ethVault, admin, user):
    timeLock = ethVault.timeLock()

    # not admin
    with brownie.reverts("!auth"):
        ethVault.setDepositLimit(123, {"from": user})

    # time lock
    ethVault.setDepositLimit(123, {"from": timeLock})
    assert ethVault.depositLimit() == 123

    # admin
    ethVault.setDepositLimit(321, {"from": admin})
    assert ethVault.depositLimit() == 321
