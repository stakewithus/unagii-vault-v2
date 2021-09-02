import brownie
from brownie import ZERO_ADDRESS


def test_set_treasury(strategyTest, admin, user):
    strategy = strategyTest

    # not auth
    with brownie.reverts("!auth"):
        strategy.setTreasury(user, {"from": user})

    # zero address
    with brownie.reverts("treasury = 0 address"):
        strategy.setTreasury(ZERO_ADDRESS, {"from": admin})

    tx = strategy.setTreasury(user, {"from": admin})
    assert strategy.treasury() == user
    assert tx.events["SetTreasury"].values() == [user]
