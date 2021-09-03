import brownie


def test_harvest(strategyTest, testVault, admin, user):
    strategy = strategyTest
    vault = testVault

    # not auth
    with brownie.reverts("!auth"):
        strategy.harvest(0, {"from": user})

    # test harvest
    strategy.harvest(0, {"from": admin})
