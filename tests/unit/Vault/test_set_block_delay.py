import brownie


def test_set_block_delay(vault, admin, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setBlockDelay(123, {"from": user})

    # delay = 0
    with brownie.reverts("delay out of range"):
        vault.setBlockDelay(0, {"from": admin})

    # delay > max
    with brownie.reverts("delay out of range"):
        vault.setBlockDelay(1001, {"from": admin})

    # time lock can call
    vault.setBlockDelay(123, {"from": timeLock})
    assert vault.blockDelay() == 123

    # admin can call
    vault.setBlockDelay(321, {"from": admin})
    assert vault.blockDelay() == 321