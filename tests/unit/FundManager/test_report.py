import brownie
from brownie import ZERO_ADDRESS


def test_report(fundManager, token, admin, testStrategy, user):
    strategy = testStrategy
    timeLock = fundManager.timeLock()

    # revert if not active strategy
    with brownie.reverts("!active"):
        fundManager.report(0, 0, {"from": strategy})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 11, 22, {"from": admin})

    # revert if gain > 0 and loss > 0
    with brownie.reverts("gain and loss > 0"):
        fundManager.report(1, 1, {"from": strategy})

    # revert if token balance < gain
    with brownie.reverts():
        fundManager.report(1, 0, {"from": strategy})

    # gain > 0
    token.mint(strategy, 1000)
    token.approve(fundManager, 2 ** 256 - 1, {"from": strategy})

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

    gain = 1

    before = snapshot()
    tx = fundManager.report(gain, 0, {"from": strategy})
    after = snapshot()

    assert after["token"]["fundManager"] == before["token"]["fundManager"] + gain
    assert after["token"]["strategy"] == before["token"]["strategy"] - gain

    assert tx.events["Report"].values() == [
        strategy,
        gain,
        0,
        after["fundManager"]["debt"],
    ]

    # loss > 0
    token.mint(fundManager, 1000)
    fundManager.borrow(100, {"from": strategy})

    loss = 1

    before = snapshot()
    tx = fundManager.report(0, loss, {"from": strategy})
    after = snapshot()

    assert after["token"]["fundManager"] == before["token"]["fundManager"]
    assert after["token"]["strategy"] == before["token"]["strategy"]
    assert (
        after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"] - loss
    )
    assert after["fundManager"]["debt"] == before["fundManager"]["debt"] - loss

    assert tx.events["Report"].values() == [
        strategy,
        0,
        loss,
        after["fundManager"]["debt"],
    ]
