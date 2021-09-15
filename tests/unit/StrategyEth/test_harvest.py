import brownie


def test_harvest(strategyEthTest, admin, user, treasury):
    strategy = strategyEthTest

    # not auth
    with brownie.reverts("!auth"):
        strategy.harvest(0, {"from": user})

    # profit < min profit
    with brownie.reverts("!auth"):
        strategy.harvest(2 ** 256 - 1, {"from": user})

    # test harvest
    def snapshot():
        return {"eth": {"strategy": strategy.balance(), "treasury": treasury.balance()}}

    before = snapshot()
    strategy.harvest(0, {"from": admin})
    after = snapshot()

    assert after["eth"]["strategy"] >= before["eth"]["strategy"]
    assert after["eth"]["treasury"] >= before["eth"]["treasury"]
