import brownie
import pytest


def test_set_perf_fee(strategyEthTest, admin, user):
    # not auth
    with brownie.reverts("!auth"):
        strategyEthTest.setPerfFee(0, {"from": user})

    # fee > cap
    with brownie.reverts("fee > cap"):
        strategyEthTest.setPerfFee(2001, {"from": admin})

    strategyEthTest.setPerfFee(2000, {"from": admin})
    assert strategyEthTest.perfFee() == 2000
