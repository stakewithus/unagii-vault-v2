import brownie
from brownie import ZERO_ADDRESS


def test_repay(ethVault, admin, testStrategyEth, user):
    vault = ethVault
    strategy = testStrategyEth
    timeLock = vault.timeLock()

    deposit_amount = 100

    # deposit into vault
    vault.deposit(1, {"from": user, "value": deposit_amount})

    # revert if not approved strategy
    with brownie.reverts("!approved strategy"):
        vault.repay({"from": strategy})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 1, {"from": admin})

    # revert if repay = 0
    with brownie.reverts("repay = 0"):
        vault.repay({"from": strategy})

    # test borrow
    def snapshot():
        return {
            "eth": {"vault": vault.balance(), "strategy": strategy.balance()},
            "vault": {
                "totalAssets": vault.totalAssets(),
                "totalDebt": vault.totalDebt(),
                "strategy": {
                    "debt": vault.strategies(strategy)["debt"],
                },
            },
        }

    borrow_amount = vault.calcMaxBorrow(strategy)
    vault.borrow(borrow_amount, {"from": strategy})

    repay_amount = borrow_amount / 2

    before = snapshot()
    tx = vault.repay({"from": strategy, "value": repay_amount})
    after = snapshot()

    assert after["eth"]["vault"] == before["eth"]["vault"] + repay_amount
    assert after["eth"]["strategy"] == before["eth"]["strategy"] - repay_amount
    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"]
    assert after["vault"]["totalDebt"] == before["vault"]["totalDebt"] - repay_amount
    assert (
        after["vault"]["strategy"]["debt"]
        == before["vault"]["strategy"]["debt"] - repay_amount
    )

    assert tx.events["Repay"].values() == [strategy, repay_amount]
