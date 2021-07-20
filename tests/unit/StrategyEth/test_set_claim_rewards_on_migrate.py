import brownie
import pytest


def test_set_claim_rewards_on_migrate(strategyEthTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyEthTest.setClaimRewardsOnMigrate(False, {"from": user})

    tx = strategyEthTest.setClaimRewardsOnMigrate(False, {"from": admin})
    assert strategyEthTest.claimRewardsOnMigrate() == False
