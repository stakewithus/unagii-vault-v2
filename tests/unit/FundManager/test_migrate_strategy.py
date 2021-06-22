import brownie
from brownie import ZERO_ADDRESS
import pytest

N = 20  # max active strategies


def test_migrate_strategy(
    chain, fundManager, testStrategy, TestStrategy, token, admin, user
):
    strat = testStrategy
    newStrat = TestStrategy.deploy(fundManager, token, {"from": admin})

    # fund strat with token
    token.mint(strat, 100)

    # test not auth
    with brownie.reverts("!auth"):
        fundManager.migrateStrategy(strat, newStrat, {"from": user})

    # test old strategy not active
    with brownie.reverts("old !active"):
        fundManager.migrateStrategy(ZERO_ADDRESS, newStrat, {"from": admin})

    timeLock = fundManager.timeLock()
    fundManager.approveStrategy(strat, {"from": timeLock})
    fundManager.addStrategyToQueue(strat, 1, 2, 3, {"from": timeLock})

    # test new strategy not approved
    with brownie.reverts("new !approved"):
        fundManager.migrateStrategy(strat, newStrat, {"from": admin})

    fundManager.approveStrategy(newStrat, {"from": timeLock})

    # test new strategy not activated
    fundManager.addStrategyToQueue(newStrat, 1, 2, 3, {"from": admin})

    with brownie.reverts("activated"):
        fundManager.migrateStrategy(strat, newStrat, {"from": admin})

    chain.undo(2)

    # test migrate strategy
    def snapshot():
        return {
            "queue": [fundManager.queue(i) for i in range(N)],
            "old": fundManager.strategies(strat),
            "new": fundManager.strategies(newStrat),
            "token": {
                "old": token.balanceOf(strat),
                "new": token.balanceOf(newStrat),
            },
        }

    before = snapshot()
    tx = fundManager.migrateStrategy(strat, newStrat, {"from": admin})
    after = snapshot()

    assert tx.events["MigrateStrategy"].values() == [strat, newStrat]

    assert after["new"]["approved"]
    assert after["new"]["active"]
    assert after["new"]["activated"]
    assert after["new"]["debtRatio"] == before["old"]["debtRatio"]
    assert after["new"]["debt"] == before["old"]["debt"]
    assert after["new"]["minBorrow"] == before["old"]["minBorrow"]
    assert after["new"]["maxBorrow"] == before["old"]["maxBorrow"]

    assert after["old"]["approved"]
    assert not after["old"]["active"]
    assert after["old"]["activated"]
    assert after["old"]["debtRatio"] == 0
    assert after["old"]["debt"] == 0
    assert after["old"]["minBorrow"] == 0
    assert after["old"]["maxBorrow"] == 0

    assert before["queue"][0] == strat
    assert after["queue"][0] == newStrat

    # check migrate was called
    assert after["token"]["new"] == before["token"]["old"]
    assert after["token"]["new"] > 0
    assert after["token"]["old"] == 0
