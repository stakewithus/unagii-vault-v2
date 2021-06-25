import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_set_treasury(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.setTreasury(user, {"from": user})

    # zero address
    with brownie.reverts("treasury = 0 address"):
        strategyTest.setTreasury(ZERO_ADDRESS, {"from": admin})

    tx = strategyTest.setTreasury(user, {"from": admin})
    assert strategyTest.treasury() == user
    assert tx.events["SetTreasury"].values() == [user]
