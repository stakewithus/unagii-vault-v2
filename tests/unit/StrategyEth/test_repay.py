import brownie


def test_repay(strategyEthTest, testEthVault, admin, user):
    strategy = strategyEthTest
    vault = testEthVault

    amount = 100
    admin.transfer(strategy, amount)

    # not auth
    with brownie.reverts("!auth"):
        strategy.repay(0, 0, {"from": user})

    # repay = 0
    with brownie.reverts("repay = 0"):
        strategy.repay(0, 0, {"from": admin})

    # repaid < min
    with brownie.reverts("repaid < min"):
        strategy.repay(amount, amount + 1, {"from": admin})

    # test repay amount <= balance of eth in strategy
    def snapshot():
        return {"eth": {"strategy": strategy.balance(), "vault": vault.balance()}}

    before = snapshot()
    strategy.repay(amount, amount, {"from": admin})
    after = snapshot()

    assert after["eth"]["strategy"] == before["eth"]["strategy"] - amount
    assert after["eth"]["vault"] == before["eth"]["vault"] + amount

    # test repay amount >= balance of eth in strategy
    admin.transfer(strategy, amount)

    before = snapshot()
    strategy.repay(amount + 1, amount, {"from": admin})
    after = snapshot()

    assert after["eth"]["strategy"] == before["eth"]["strategy"] - amount
    assert after["eth"]["vault"] == before["eth"]["vault"] + amount