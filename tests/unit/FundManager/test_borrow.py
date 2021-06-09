import brownie
from brownie import ZERO_ADDRESS


def test_borrow(fundManager, token, admin, keeper, guardian, testStrategy, user):
    strategy = testStrategy

    # revert if paused
    fundManager.setPause(True, {"from": guardian})

    with brownie.reverts("paused"):
        fundManager.borrow(0, {"from": strategy})

    fundManager.setPause(False, {"from": guardian})

    # revert if not active strategy
    with brownie.reverts("!active"):
        fundManager.borrow(0, {"from": strategy})

    fundManager.approveStrategy(strategy, {"from": admin})
    fundManager.addStrategyToQueue(strategy, 1, 11, 22, {"from": admin})

    # revert if borrow = 0
    with brownie.reverts("borrow = 0"):
        fundManager.borrow(0, {"from": strategy})

    token.mint(fundManager, 100)

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

    amount = 12

    before = snapshot()
    tx = fundManager.borrow(amount, {"from": strategy})
    after = snapshot()

    strat = fundManager.strategies(strategy)

    assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount
    assert after["token"]["strategy"] == before["token"]["strategy"] + amount
    assert (
        after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"] + amount
    )
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] + amount

    assert tx.events["Borrow"].values() == [strategy, amount]
