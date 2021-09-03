import brownie


def test_set_skip_harvest(strategyTest, admin, user):
    strategy = strategyTest

    # not auth
    with brownie.reverts("!auth"):
        strategy.setSkipHarvest(False, {"from": user})

    strategy.setSkipHarvest(False, {"from": admin})
    assert strategy.skipHarvest() == False
