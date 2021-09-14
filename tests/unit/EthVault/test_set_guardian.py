import brownie


def test_set_guardian(chain, ethVault, admin, user):
    vault = ethVault
    timeLock = vault.timeLock()

    with brownie.reverts("!auth"):
        vault.setGuardian(user, {"from": user})

    # admin can call
    vault.setGuardian(user, {"from": admin})
    assert vault.guardian() == user

    chain.undo()
    assert vault.guardian() != user

    # time lock can call
    tx = vault.setGuardian(user, {"from": timeLock})
    assert vault.guardian() == user
    assert tx.events["SetGuardian"].values() == [user]
