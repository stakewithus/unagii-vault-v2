import brownie


def test_set_admin(strategyV2Test, admin, user):
    strategy = strategyV2Test

    # not auth
    with brownie.reverts("!auth"):
        strategy.setAdmin(user, {"from": user})

    tx = strategy.setAdmin(user, {"from": admin})
    assert strategy.admin() == user
    assert tx.events["SetAdmin"].values() == [user]
