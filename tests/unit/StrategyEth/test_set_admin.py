import brownie
import pytest


def test_set_admin(strategyEthTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyEthTest.setAdmin(user, {"from": user})

    tx = strategyEthTest.setAdmin(user, {"from": admin})
    assert strategyEthTest.admin() == user
    assert tx.events["SetAdmin"].values() == [user]
