import brownie


def test_set_pause(ethVault, admin, guardian, user):
    vault = ethVault
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setPause(True, {"from": user})

    # time lock can call
    tx = vault.setPause(True, {"from": timeLock})
    assert vault.paused()
    assert tx.events["SetPause"].values() == [True]

    vault.setPause(False, {"from": timeLock})
    assert not vault.paused()

    # admin can call
    vault.setPause(True, {"from": admin})
    assert vault.paused()

    vault.setPause(False, {"from": admin})
    assert not vault.paused()

    # guardian can call
    vault.setPause(True, {"from": guardian})
    assert vault.paused()

    vault.setPause(False, {"from": guardian})
    assert not vault.paused()
