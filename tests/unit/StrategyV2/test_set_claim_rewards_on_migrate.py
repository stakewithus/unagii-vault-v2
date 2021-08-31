import brownie


def test_set_claim_rewards_on_migrate(strategyV2Test, admin, user):
    strategy = strategyV2Test

    # not auth
    with brownie.reverts("!auth"):
        strategy.setClaimRewardsOnMigrate(False, {"from": user})

    strategy.setClaimRewardsOnMigrate(False, {"from": admin})
    assert strategy.claimRewardsOnMigrate() == False
