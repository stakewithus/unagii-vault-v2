import brownie
import pytest


def test_set_deposit_limit(vault, admin, keeper, user):
    # not admin
    with brownie.reverts("!auth"):
        vault.setDepositLimit(123, {"from": user})

    # admin
    vault.setDepositLimit(123, {"from": admin})
    assert vault.depositLimit() == 123

    # keeper
    vault.setDepositLimit(321, {"from": keeper})
    assert vault.depositLimit() == 321
