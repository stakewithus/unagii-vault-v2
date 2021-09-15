import brownie


def test_withdraw(strategyEthTest, testEthVault, admin, user):
    strategy = strategyEthTest
    vault = testEthVault

    amount = 100
    admin.transfer(strategy, amount)

    # not vault
    with brownie.reverts("!vault"):
        strategy.withdraw(0, {"from": user})

    # withdraw = 0
    with brownie.reverts("withdraw = 0"):
        strategy.withdraw(0, {"from": vault})

    # test withdraw amount <= balance of token in strategy
    def snapshot():
        return {"eth": {"strategy": strategy.balance(), "vault": vault.balance()}}

    before = snapshot()
    strategy.withdraw(amount, {"from": vault})
    after = snapshot()

    assert after["eth"]["strategy"] == before["eth"]["strategy"] - amount
    assert after["eth"]["vault"] == before["eth"]["vault"] + amount

    # test withdraw amount >= balance of token in strategy
    admin.transfer(strategy, amount)

    before = snapshot()
    strategy.withdraw(amount + 1, {"from": vault})
    after = snapshot()

    assert after["eth"]["strategy"] == before["eth"]["strategy"] - amount
    assert after["eth"]["vault"] == before["eth"]["vault"] + amount