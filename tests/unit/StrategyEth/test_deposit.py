import brownie


def test_deposit(strategyEthTest, testEthVault, admin, user):
    strategy = strategyEthTest
    vault = testEthVault

    amount = 100
    admin.transfer(vault, amount)

    # not auth
    with brownie.reverts("!auth"):
        strategy.deposit(0, 0, {"from": user})

    # borrowed < min
    with brownie.reverts("borrowed < min"):
        strategy.deposit(amount, amount + 1, {"from": admin})

    # test deposit > 0
    def snapshot():
        return {"eth": {"strategy": strategy.balance()}}

    before = snapshot()
    strategy.deposit(amount, 1, {"from": admin})
    after = snapshot()

    assert after["eth"]["strategy"] == before["eth"]["strategy"] + amount

    # test deposit == 0
    before = snapshot()
    strategy.deposit(0, 1, {"from": admin})
    after = snapshot()

    assert after["eth"]["strategy"] == before["eth"]["strategy"]
