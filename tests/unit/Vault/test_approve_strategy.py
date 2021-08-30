import brownie
from brownie import ZERO_ADDRESS


def test_approve_strategy(vault, token, testStrategy, user):
    strategy = testStrategy
    timeLock = vault.timeLock()

    # revert if not time lock
    with brownie.reverts("!time lock"):
        vault.approveStrategy(strategy, {"from": user})

    # revert if strategy.vault != vault
    strategy.setVault(ZERO_ADDRESS)
    with brownie.reverts("strategy vault != vault"):
        vault.approveStrategy(strategy, {"from": timeLock})

    strategy.setVault(vault)

    # revert if strategy.token != token
    strategy.setToken(ZERO_ADDRESS)
    with brownie.reverts("strategy token != token"):
        vault.approveStrategy(strategy, {"from": timeLock})

    strategy.setToken(token)

    tx = vault.approveStrategy(strategy, {"from": timeLock})
    strat = vault.strategies(strategy)

    assert strat["approved"]
    assert not strat["active"]
    assert strat["debtRatio"] == 0
    assert strat["debt"] == 0

    assert tx.events["ApproveStrategy"].values() == [strategy]

    # revert if approved
    with brownie.reverts("approved"):
        vault.approveStrategy(strategy, {"from": timeLock})
