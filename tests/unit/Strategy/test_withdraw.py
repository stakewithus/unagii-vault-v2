import brownie


def test_withdraw(strategyTest, testVault, token, admin, user):
    strategy = strategyTest
    vault = testVault

    amount = 100
    token.mint(vault, amount)

    # not auth
    with brownie.reverts("!auth"):
        strategy.deposit(0, 0, {"from": user})
