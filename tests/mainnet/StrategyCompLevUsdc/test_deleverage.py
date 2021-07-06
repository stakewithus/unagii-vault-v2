import brownie
import pytest


def test_deleverage(strategy, usdcFundManager, admin, usdc, usdc_whale):
    token = usdc
    whale = usdc_whale

    fundManager = usdcFundManager

    deposit_amount = 10 ** 6
    token.transfer(fundManager, deposit_amount, {"from": whale})

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, deposit_amount, {"from": admin})

    (supplied, borrowed, market_col, safe_col) = strategy.getLivePosition.call()
    # print(supplied, borrowed, market_col, safe_col)

    # calculate target supply
    s = supplied
    b = borrowed
    r = int(s - b * 10 ** 18 / safe_col)
    for i in range(10):
        if r >= b:
            r = b
        s -= r
        b -= r
        r = int(s - b * 10 ** 18 / safe_col)
        # print(s, b)

    def snapshot():
        (supplied, borrowed, market_col, safe_col) = strategy.getLivePosition.call()
        return {
            "supplied": supplied,
            "borrowed": borrowed,
            "market_col": market_col,
            "safe_col": safe_col,
        }

    before = snapshot()
    tx = strategy.deleverage(s, {"from": admin})
    after = snapshot()

    print(before)
    print(after)
    # # for e in tx.events:
    # #     print(e)

    assert abs(after["supplied"] - s) <= 0.001 * 10 ** 6
