import brownie
import pytest


def test_set_worker(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.setWorker(user, {"from": user})

    tx = strategyTest.setWorker(user, {"from": admin})
    assert strategyTest.worker() == user
    assert tx.events["SetWorker"].values() == [user]
