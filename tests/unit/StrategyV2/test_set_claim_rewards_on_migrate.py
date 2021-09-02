import brownie


def test_set_claim_rewards_on_migrate(strategyTest, admin, user):
    strategy = strategyTest

    # not auth
    with brownie.reverts("!auth"):
        strategy.setClaimRewardsOnMigrate(False, {"from": user})

    strategy.setClaimRewardsOnMigrate(False, {"from": admin})
    assert strategy.claimRewardsOnMigrate() == False
