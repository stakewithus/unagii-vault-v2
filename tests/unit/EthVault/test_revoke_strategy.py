import brownie


def test_revoke_strategy(ethVault, admin, testStrategyEth, user):
    vault = ethVault
    strategy = testStrategyEth
    timeLock = vault.timeLock()

    # revert if not authorized
    with brownie.reverts("!auth"):
        vault.revokeStrategy(strategy, {"from": user})

    # revert if not approved
    with brownie.reverts("!approved"):
        vault.revokeStrategy(strategy, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})

    # revert if active
    vault.activateStrategy(strategy, 1, {"from": admin})

    with brownie.reverts("active"):
        vault.revokeStrategy(strategy, {"from": admin})

    vault.deactivateStrategy(strategy, {"from": admin})

    tx = vault.revokeStrategy(strategy, {"from": admin})
    strat = vault.strategies(strategy)

    assert not strat["approved"]
    assert tx.events["RevokeStrategy"].values() == [strategy]
