import brownie
import pytest


def test_set_block_delay(vault, admin, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setBlockDelay(123, {"from": user})

    # delay = 0
    with brownie.reverts("delay = 0"):
        vault.setBlockDelay(0, {"from": admin})

    # time lock
    vault.setBlockDelay(123, {"from": timeLock})
    assert vault.blockDelay() == 123

    # admin
    vault.setBlockDelay(321, {"from": admin})
    assert vault.blockDelay() == 321