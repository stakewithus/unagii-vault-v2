import brownie
from brownie import ZERO_ADDRESS


def test_borrow(ethFundManager, admin, guardian, testStrategyEth, user):
    fundManager = ethFundManager
    strategy = testStrategyEth
    timeLock = fundManager.timeLock()

    # revert if paused
    fundManager.setPause(True, {"from": guardian})

    with brownie.reverts("paused"):
        fundManager.borrow(0, {"from": strategy})

    fundManager.setPause(False, {"from": guardian})

    # revert if not active strategy
    with brownie.reverts("!active"):
        fundManager.borrow(0, {"from": strategy})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 11, 22, {"from": admin})

    # revert if borrow = 0
    with brownie.reverts("borrow = 0"):
        fundManager.borrow(0, {"from": strategy})

    user.transfer(fundManager, 100)

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

    amount = 12

    before = snapshot()
    tx = fundManager.borrow(amount, {"from": strategy})
    after = snapshot()

    strat = fundManager.strategies(strategy)

    diff = before["eth"]["fundManager"] - after["eth"]["fundManager"]
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] - amount
    assert after["eth"]["strategy"] == before["eth"]["strategy"] + amount
    assert (
        after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"] + amount
    )
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] + amount

    assert tx.events["Borrow"].values() == [strategy, amount, diff]
