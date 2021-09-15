import brownie


def test_set_admin(strategyEthTest, admin, user):
    strategy = strategyEthTest

    # not auth
    with brownie.reverts("!auth"):
        strategy.setAdmin(user, {"from": user})

    tx = strategy.setAdmin(user, {"from": admin})
    assert strategy.admin() == user
    assert tx.events["SetAdmin"].values() == [user]
