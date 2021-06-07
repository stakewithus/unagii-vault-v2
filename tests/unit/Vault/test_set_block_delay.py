import brownie
import pytest


def test_set_block_delay(vault, admin, keeper, user):
    # not admin
    with brownie.reverts("!auth"):
        vault.setBlockDelay(123, {"from": user})

    # delay = 0
    with brownie.reverts("delay = 0"):
        vault.setBlockDelay(0, {"from": admin})

    # admin
    vault.setBlockDelay(123, {"from": admin})
    assert vault.blockDelay() == 123

    # keeper
    vault.setBlockDelay(321, {"from": keeper})
    assert vault.blockDelay() == 321