import brownie


def test_authorize(strategyEthTest, admin, user):
    strategy = strategyEthTest

    # not auth
    with brownie.reverts("!auth"):
        strategy.authorize(user, True, {"from": user})

    tx = strategy.authorize(user, True, {"from": admin})
    assert strategy.authorized(user)
    assert tx.events["Authorize"].values() == [user, True]
