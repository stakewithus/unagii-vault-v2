import brownie
from brownie import ZERO_ADDRESS


def test_repay(fundManager, token, admin, testErc20Strategy, user):
    strategy = testErc20Strategy
    timeLock = fundManager.timeLock()

    # revert if not approved strategy
    with brownie.reverts("!approved"):
        fundManager.repay(0, {"from": strategy})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 11, 22, {"from": admin})

    token.mint(fundManager, 1000)
    token.mint(strategy, 1000)

    amount = 12
    fundManager.borrow(amount, {"from": strategy})

    # revert if repay = 0
    with brownie.reverts("repay = 0"):
        fundManager.repay(0, {"from": strategy})

    def snapshot():
        return {
            "token": {
                "fundManager": token.balanceOf(fundManager),
                "strategy": token.balanceOf(strategy),
            },
            "fundManager": {
                "totalDebt": fundManager.totalDebt(),
                "debt": fundManager.strategies(strategy)["debt"],
            },
        }

    amount = 11
    token.approve(fundManager, amount, {"from": strategy})

    before = snapshot()
    tx = fundManager.repay(amount, {"from": strategy})
    after = snapshot()

    diff = after["token"]["fundManager"] - before["token"]["fundManager"]
    assert after["token"]["fundManager"] == before["token"]["fundManager"] + amount
    assert after["token"]["strategy"] == before["token"]["strategy"] - amount
    assert (
        after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"] - amount
    )
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] - amount

    assert tx.events["Repay"].values() == [strategy, amount, diff]
