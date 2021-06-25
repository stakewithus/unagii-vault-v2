import brownie
import pytest


def test_set_guardian(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.setGuardian(user, {"from": user})

    tx = strategyTest.setGuardian(user, {"from": admin})
    assert strategyTest.guardian() == user
    assert tx.events["SetGuardian"].values() == [user]
