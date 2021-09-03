import brownie


def test_repay(strategyTest, testVault, token, admin, user):
    strategy = strategyTest
    vault = testVault

    amount = 100
    token.mint(strategy, amount)

    # not auth
    with brownie.reverts("!auth"):
        strategy.repay(0, 0, {"from": user})

    # repay = 0
    with brownie.reverts("repay = 0"):
        strategy.repay(0, 0, {"from": admin})

    # repaid < min
    with brownie.reverts("repaid < min"):
        strategy.repay(amount, amount + 1, {"from": admin})

    # test repay amount <= balance of token in strategy
    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "vault": token.balanceOf(vault),
            }
        }

    before = snapshot()
    strategy.repay(amount, amount, {"from": admin})
    after = snapshot()

    assert after["token"]["strategy"] == before["token"]["strategy"] - amount
    assert after["token"]["vault"] == before["token"]["vault"] + amount

    # test repay amount >= balance of token in strategy
    token.mint(strategy, amount)

    before = snapshot()
    strategy.repay(amount + 1, amount, {"from": admin})
    after = snapshot()

    assert after["token"]["strategy"] == before["token"]["strategy"] - amount
    assert after["token"]["vault"] == before["token"]["vault"] + amount