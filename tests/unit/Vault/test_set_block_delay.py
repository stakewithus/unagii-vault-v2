import brownie
import pytest


def test_set_block_delay(vault, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.setBlockDelay(123, {"from": user})

    # delay = 0
    with brownie.reverts("delay = 0"):
        vault.setBlockDelay(0, {"from": admin})

    # admin can call
    vault.setBlockDelay(123, {"from": admin})
    assert vault.blockDelay() == 123
