import brownie


def test_set_min_max_profit(perfFeeTest, user):
    # min profit >= max profit
    with brownie.reverts("min profit >= max profit"):
        perfFeeTest.setMinMaxProfit(1, 1, {"from": user})

    tx = perfFeeTest.setMinMaxProfit(1, 2, {"from": user})

    assert tx.events["SetMinMaxProfit"].values() == [1, 2]

    assert perfFeeTest.minProfit() == 1
    assert perfFeeTest.maxProfit() == 2
