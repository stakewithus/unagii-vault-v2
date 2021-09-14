import brownie


def test_set_worker(chain, ethVault, admin, user):
    vault = ethVault
    timeLock = vault.timeLock()

    with brownie.reverts("!auth"):
        vault.setWorker(user, {"from": user})

    # admin can call
    vault.setWorker(user, {"from": admin})
    assert vault.worker() == user

    chain.undo()
    assert vault.worker() != user

    # time lock can call
    tx = vault.setWorker(user, {"from": timeLock})
    assert vault.worker() == user
    assert tx.events["SetWorker"].values() == [user]
