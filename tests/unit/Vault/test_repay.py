import brownie
from brownie import ZERO_ADDRESS


def test_repay(vault, token, admin, testStrategy, user):
    strategy = testStrategy
    timeLock = vault.timeLock()

    deposit_amount = 100

    # deposit into vault
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    # revert if not approved strategy
    with brownie.reverts("!approved strategy"):
        vault.repay(0, {"from": strategy})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 1, {"from": admin})

    # revert if repay = 0
    with brownie.reverts("repay = 0"):
        vault.repay(0, {"from": strategy})

    # test borrow
    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "strategy": token.balanceOf(strategy),
            },
            "vault": {
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
                "strategy": {
                    "debt": vault.strategies(strategy)["debt"],
                },
            },
        }

    borrow_amount = vault.calcMaxBorrow(strategy)
    vault.borrow(borrow_amount, {"from": strategy})

    repay_amount = borrow_amount / 2
    token.approve(vault, repay_amount, {"from": strategy})

    before = snapshot()
    tx = vault.repay(repay_amount, {"from": strategy})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"] + repay_amount
    assert after["token"]["strategy"] == before["token"]["strategy"] - repay_amount
    assert (
        after["vault"]["balanceOfVault"]
        == before["vault"]["balanceOfVault"] + repay_amount
    )
    assert after["vault"]["debt"] == before["vault"]["debt"] - repay_amount
    assert (
        after["vault"]["strategy"]["debt"]
        == before["vault"]["strategy"]["debt"] - repay_amount
    )

    assert tx.events["Repay"].values() == [strategy, repay_amount]
