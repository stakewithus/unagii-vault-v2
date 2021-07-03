import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_set_treasury(strategyEthTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyEthTest.setTreasury(user, {"from": user})

    # zero address
    with brownie.reverts("treasury = 0 address"):
        strategyEthTest.setTreasury(ZERO_ADDRESS, {"from": admin})

    tx = strategyEthTest.setTreasury(user, {"from": admin})
    assert strategyEthTest.treasury() == user
    assert tx.events["SetTreasury"].values() == [user]
