import brownie
from brownie import ZERO_ADDRESS


def test_repay(ethFundManager, admin, testStrategyEth, user):
    fundManager = ethFundManager
    strategy = testStrategyEth
    timeLock = fundManager.timeLock()

    # revert if not approved strategy
    with brownie.reverts("!approved"):
        fundManager.repay(0, {"from": strategy})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 11, 22, {"from": admin})

    user.transfer(fundManager, 1000)
    user.transfer(strategy, 1000)

    amount = 12
    fundManager.borrow(amount, {"from": strategy})

    # revert if repay = 0
    with brownie.reverts("repay = 0"):
        fundManager.repay(0, {"from": strategy})

    def snapshot():
        return {
            "eth": {
                "fundManager": fundManager.balance(),
                "strategy": strategy.balance(),
            },
            "fundManager": {
                "totalDebt": fundManager.totalDebt(),
                "debt": fundManager.strategies(strategy)["debt"],
            },
        }

    amount = 11

    before = snapshot()
    tx = fundManager.repay(amount, {"from": strategy, "value": amount})
    after = snapshot()

    diff = after["eth"]["fundManager"] - before["eth"]["fundManager"]
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] + amount
    assert after["eth"]["strategy"] == before["eth"]["strategy"] - amount
    assert (
        after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"] - amount
    )
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] - amount

    assert tx.events["Repay"].values() == [strategy, amount, diff]
