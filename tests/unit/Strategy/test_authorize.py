import brownie
import pytest


def test_authorize(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.authorize(user, True, {"from": user})

    tx = strategyTest.authorize(user, True, {"from": admin})
    assert strategyTest.authorized(user)
    assert tx.events["Authorize"].values() == [user, True]
