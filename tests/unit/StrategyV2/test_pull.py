import brownie


def test_pull(strategyV2Test, token, admin, user):
    strategy = strategyV2Test

    token.mint(admin, 1000)
    token.approve(strategy, 1000, {"from": admin})

    # not auth
    with brownie.reverts("!auth"):
        strategy.pull(admin, 1000, {"from": user})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
            }
        }

    before = snapshot()
    strategy.pull(admin, 1000, {"from": admin})
    after = snapshot()

    diff = after["token"]["strategy"] - before["token"]["strategy"]
    assert diff == 1000