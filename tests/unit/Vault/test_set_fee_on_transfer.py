import brownie
import pytest


def test_set_fee_on_transfer(vault, admin, keeper, user):
    # not auth
    with brownie.reverts("!auth"):
        vault.setFeeOnTransfer(True, {"from": user})

    # admin
    vault.setFeeOnTransfer(True, {"from": admin})
    assert vault.feeOnTransfer()

    # keeper
    vault.setFeeOnTransfer(False, {"from": keeper})
    assert not vault.feeOnTransfer()
