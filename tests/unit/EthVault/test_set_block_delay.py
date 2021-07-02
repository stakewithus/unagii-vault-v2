import brownie
import pytest


def test_set_block_delay(ethVault, admin, user):
    timeLock = ethVault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        ethVault.setBlockDelay(123, {"from": user})

    # delay = 0
    with brownie.reverts("delay = 0"):
        ethVault.setBlockDelay(0, {"from": admin})

    # time lock
    ethVault.setBlockDelay(123, {"from": timeLock})
    assert ethVault.blockDelay() == 123

    # admin
    ethVault.setBlockDelay(321, {"from": admin})
    assert ethVault.blockDelay() == 321