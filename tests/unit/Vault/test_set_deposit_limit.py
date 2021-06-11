import brownie
import pytest


def test_set_deposit_limit(vault, admin, user):
    timeLock = vault.timeLock()

    # not admin
    with brownie.reverts("!auth"):
        vault.setDepositLimit(123, {"from": user})

    # time lock
    vault.setDepositLimit(123, {"from": timeLock})
    assert vault.depositLimit() == 123

    # admin
    vault.setDepositLimit(321, {"from": admin})
    assert vault.depositLimit() == 321
