import brownie
import pytest


def test_harvest(strategy, usdcFundManager, admin, usdc, usdc_whale):
    token = usdc
    whale = usdc_whale

    fundManager = usdcFundManager

    # deposit into fund manager
    deposit_amount = 10000 * 10 ** 6
    token.transfer(fundManager, deposit_amount, {"from": whale})

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, deposit_amount, {"from": admin})

    def snapshot():
        return {
            "token": {
                "strategy": token.balanceOf(strategy),
                "fundManager": token.balanceOf(fundManager),
            },
            "strategy": {"totalAssets": strategy.totalAssets()},
            "fundManager": {"debt": fundManager.getDebt(strategy)},
        }

    # create profit
    min_profit = 0.001 * deposit_amount
    token.transfer(strategy, min_profit, {"from": whale})

    before = snapshot()
    print(before)
    tx = strategy.harvest(1, 0, 2 ** 256 - 1, {"from": admin})
    after = snapshot()

    # print(before)
    # print(after)
    # for e in tx.events:
    #     print(e)

    assert after["strategy"]["totalAssets"] >= before["fundManager"]["debt"]
    assert after["token"]["fundManager"] >= before["token"]["fundManager"]
