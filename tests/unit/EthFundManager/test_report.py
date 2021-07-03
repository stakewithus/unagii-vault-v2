import brownie
from brownie import ZERO_ADDRESS


def test_report(ethFundManager, admin, testStrategyEth, user):
    fundManager = ethFundManager
    strategy = testStrategyEth
    timeLock = fundManager.timeLock()

    # revert if not active strategy
    with brownie.reverts("!active"):
        fundManager.report(0, 0, {"from": strategy})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 11, 22, {"from": admin})

    # revert if gain > 0 and loss > 0
    with brownie.reverts("gain and loss > 0"):
        fundManager.report(1, 1, {"from": strategy})

    # revert if eth balance < gain
    with brownie.reverts():
        fundManager.report(1, 0, {"from": strategy})

    # gain > 0
    user.transfer(strategy, 1000)

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

    gain = 1

    before = snapshot()
    tx = fundManager.report(gain, 0, {"from": strategy, "value": gain})
    after = snapshot()

    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] + gain
    assert after["eth"]["strategy"] == before["eth"]["strategy"] - gain

    assert tx.events["Report"].values() == [
        strategy,
        gain,
        0,
        after["fundManager"]["debt"],
    ]

    # loss > 0
    user.transfer(fundManager, 1000)
    fundManager.borrow(100, {"from": strategy})

    loss = 1

    before = snapshot()
    tx = fundManager.report(0, loss, {"from": strategy})
    after = snapshot()

    assert after["eth"]["fundManager"] == before["eth"]["fundManager"]
    assert after["eth"]["strategy"] == before["eth"]["strategy"]
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
