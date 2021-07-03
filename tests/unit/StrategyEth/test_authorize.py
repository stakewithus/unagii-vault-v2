import brownie
import pytest


def test_authorize(strategyEthTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyEthTest.authorize(user, True, {"from": user})

    tx = strategyEthTest.authorize(user, True, {"from": admin})
    assert strategyEthTest.authorized(user)
    assert tx.events["Authorize"].values() == [user, True]
