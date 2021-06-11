import brownie
import pytest


def test_set_fee_on_transfer(vault, admin, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setFeeOnTransfer(True, {"from": user})

    # time lock
    vault.setFeeOnTransfer(True, {"from": timeLock})
    assert vault.feeOnTransfer()

    # admin
    vault.setFeeOnTransfer(False, {"from": admin})
    assert not vault.feeOnTransfer()
