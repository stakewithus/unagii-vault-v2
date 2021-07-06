import brownie
import pytest


def test_claim_rewards(strategy, wbtcFundManager, admin, wbtc, wbtc_whale):
    token = wbtc
    whale = wbtc_whale

    fundManager = wbtcFundManager

    amount = 10 * 10 ** 8
    token.transfer(fundManager, amount, {"from": whale})

    strategy.deposit(2 ** 256 - 1, amount, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
        }

    min_profit = 1

    before = snapshot()
    tx = strategy.claimRewards(min_profit, {"from": admin})
    after = snapshot()

    print(before)
    print(after)
    for e in tx.events:
        print(e)

    event = tx.events[-1]
    profit = event["profit"]

    assert profit >= min_profit
    assert after["token"]["strategy"] >= before["token"]["strategy"] + profit
    assert (
        after["strategy"]["totalAssets"] >= before["strategy"]["totalAssets"] + profit
    )
