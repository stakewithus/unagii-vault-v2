import brownie
import pytest


def test_set_claim_rewards_on_migrate(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.setClaimRewardsOnMigrate(False, {"from": user})

    tx = strategyTest.setClaimRewardsOnMigrate(False, {"from": admin})
    assert strategyTest.claimRewardsOnMigrate() == False
