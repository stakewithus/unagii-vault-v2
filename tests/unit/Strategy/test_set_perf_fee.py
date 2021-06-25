import brownie
import pytest


def test_set_perf_fee(strategyTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyTest.setPerfFee(0, {"from": user})

    # fee > cap
    with brownie.reverts("fee > cap"):
        strategyTest.setPerfFee(2001, {"from": admin})

    strategyTest.setPerfFee(2000, {"from": admin})
    assert strategyTest.perfFee() == 2000
