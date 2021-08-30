import brownie


def test_activate_strategy(vault, admin, testStrategy, user):
    strategy = testStrategy
    timeLock = vault.timeLock()

    # revert if not authorized
    with brownie.reverts("!auth"):
        vault.activateStrategy(strategy, 0, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        vault.activateStrategy(strategy, 0, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})

    # revert if debt ratio > max
    with brownie.reverts("debt ratio > max"):
        vault.activateStrategy(strategy, 100001, {"from": admin})

    def snapshot():
        return {"totalDebtRatio": vault.totalDebtRatio()}

    before = snapshot()
    tx = vault.activateStrategy(strategy, 123, {"from": admin})
    after = snapshot()

    strat = vault.strategies(strategy)

    assert strat["approved"]
    assert strat["active"]
    assert strat["debtRatio"] == 123

    assert after["totalDebtRatio"] == before["totalDebtRatio"] + strat["debtRatio"]
    assert vault.queue(0) == strategy

    assert tx.events["ActivateStrategy"].values() == [strategy]

    # revert if active
    with brownie.reverts("active"):
        vault.activateStrategy(strategy, 0, {"from": admin})
