import brownie
import pytest


def test_set_fee_on_transfer(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setFeeOnTransfer(True, {"from": user})

    # admin can call
    vault.setFeeOnTransfer(True, {"from": admin})
    assert vault.feeOnTransfer()
