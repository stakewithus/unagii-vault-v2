import brownie
import pytest


def test_claim_rewards(strategy, ethFundManager, admin, eth_whale):
    whale = eth_whale

    fundManager = ethFundManager

    amount = 10 ** 18
    eth_whale.transfer(fundManager, amount)

    strategy.deposit(2 ** 256 - 1, 1, {"from": admin})

    def snapshot():
        return {
            "eth": {"strategy": strategy.balance()},
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    min_profit = 1

    before = snapshot()
    tx = strategy.claimRewards(min_profit, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    event = tx.events[-1]
    profit = event["profit"]

    assert profit >= min_profit
    assert after["eth"]["strategy"] >= before["eth"]["strategy"] + profit
    assert (
        after["strategy"]["totalAssets"] >= before["strategy"]["totalAssets"] + profit
    )
