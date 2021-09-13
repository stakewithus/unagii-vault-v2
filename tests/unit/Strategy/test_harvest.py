import brownie


def test_harvest(strategyTest, testVault, token, admin, user, treasury):
    strategy = strategyTest
    vault = testVault

    # not auth
    with brownie.reverts("!auth"):
        strategy.harvest(0, {"from": user})

    # profit < min profit
    with brownie.reverts("!auth"):
        strategy.harvest(2 ** 256 - 1, {"from": user})

    # test harvest
    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "treasury": token.balanceOf(treasury),
            }
        }

    before = snapshot()
    strategy.harvest(1, {"from": admin})
    after = snapshot()

    assert after["token"]["strategy"] > before["token"]["strategy"]
    assert after["token"]["treasury"] > before["token"]["treasury"]
