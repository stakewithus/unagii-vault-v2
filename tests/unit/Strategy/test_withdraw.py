import brownie


def test_withdraw(strategyTest, testVault, token, admin, user):
    strategy = strategyTest
    vault = testVault

    amount = 100
    token.mint(strategy, amount)

    # not vault
    with brownie.reverts("!vault"):
        strategy.withdraw(0, {"from": user})

    # withdraw = 0
    with brownie.reverts("withdraw = 0"):
        strategy.withdraw(0, {"from": vault})

    # test withdraw amount <= balance of token in strategy
    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "vault": token.balanceOf(vault),
            }
        }

    before = snapshot()
    strategy.withdraw(amount, {"from": vault})
    after = snapshot()

    assert after["token"]["strategy"] == before["token"]["strategy"] - amount
    assert after["token"]["vault"] == before["token"]["vault"] + amount

    # test withdraw amount >= balance of token in strategy
    token.mint(strategy, amount)

    before = snapshot()
    strategy.withdraw(amount + 1, {"from": vault})
    after = snapshot()

    assert after["token"]["strategy"] == before["token"]["strategy"] - amount
    assert after["token"]["vault"] == before["token"]["vault"] + amount