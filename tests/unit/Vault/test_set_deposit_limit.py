import brownie
import pytest


def test_set_deposit_limit(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setDepositLimit(123, {"from": user})

    # admin can call
    vault.setDepositLimit(123, {"from": admin})
    assert vault.depositLimit() == 123
