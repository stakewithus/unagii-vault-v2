import brownie


def test_deposit(strategyTest, testVault, token, admin, user):
    strategy = strategyTest
    vault = testVault

    amount = 100
    token.mint(vault, amount)

    # not auth
    with brownie.reverts("!auth"):
        strategy.deposit(0, 0, {"from": user})

    # borrowed < min
    with brownie.reverts("borrowed < min"):
        strategy.deposit(amount, amount + 1, {"from": admin})

    # test deposit > 0
    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
            }
        }

    before = snapshot()
    strategy.deposit(amount, 1, {"from": admin})
    after = snapshot()

    assert after["token"]["strategy"] == before["token"]["strategy"] + amount

    # test deposit == 0
    before = snapshot()
    strategy.deposit(0, 1, {"from": admin})
    after = snapshot()

    assert after["token"]["strategy"] == before["token"]["strategy"]
