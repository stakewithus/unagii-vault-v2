import brownie
import pytest


def test_set_admin(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.setAdmin(user, {"from": user})

    tx = strategyTest.setAdmin(user, {"from": admin})
    assert strategyTest.admin() == user
    assert tx.events["SetAdmin"].values() == [user]
