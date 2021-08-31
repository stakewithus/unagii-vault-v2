import brownie


def test_set_min_max_tvl(strategyV2Test, admin, user):
    strategy = strategyV2Test

    # not auth
    with brownie.reverts("!auth"):
        strategy.setMinMaxTvl(0, 1, {"from": user})

    # min tvl >= max tvl
    with brownie.reverts("min tvl >= max tvl"):
        strategy.setMinMaxTvl(0, 0, {"from": admin})

    tx = strategy.setMinMaxTvl(0, 1, {"from": admin})

    assert tx.events["SetMinMaxTvl"].values() == [0, 1]

    assert strategy.minTvl() == 0
    assert strategy.maxTvl() == 1
