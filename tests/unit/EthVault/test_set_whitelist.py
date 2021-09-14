import brownie


def test_set_whitelist(ethVault, admin, user):
    vault = ethVault
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setWhitelist(user, True, {"from": user})

    # time lock can call
    tx = vault.setWhitelist(user, True, {"from": timeLock})
    assert vault.whitelist(user)
    assert len(tx.events) == 1
    assert tx.events["SetWhitelist"].values() == [user, True]

    vault.setWhitelist(user, False, {"from": timeLock})
    assert not vault.whitelist(user)

    # admin can call
    vault.setWhitelist(user, True, {"from": admin})
    assert vault.whitelist(user)

    vault.setWhitelist(user, False, {"from": admin})
    assert not vault.whitelist(user)
