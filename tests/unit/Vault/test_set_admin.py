import brownie


def test_set_admin(chain, vault, admin, user):
    timeLock = vault.timeLock()

    with brownie.reverts("!auth"):
        vault.setAdmin(user, {"from": user})

    # admin can call
    vault.setAdmin(user, {"from": admin})
    assert vault.admin() == user

    chain.undo()
    assert vault.admin() != user

    # time lock can call
    tx = vault.setAdmin(user, {"from": timeLock})
    assert vault.admin() == user
    assert tx.events["SetAdmin"].values() == [user]
