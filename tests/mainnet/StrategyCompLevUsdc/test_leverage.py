import brownie
import pytest


DECIMALS = 6


def test_leverage(strategy, admin, usdc, usdc_whale):
    token = usdc
    whale = usdc_whale

    deposit_amount = 10 ** DECIMALS
    token.transfer(strategy, deposit_amount, {"from": whale})
    strategy.supplyManual(deposit_amount, {"from": admin})

    (supplied, borrowed, market_col, safe_col) = strategy.getLivePosition.call()
    # print(supplied, borrowed, market_col, safe_col)

    # calculate target supply
    s = supplied
    b = borrowed
    for i in range(3):
        b = int(s * safe_col / 10 ** 18 - b)
        s += b
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
    strategy.leverage(s, {"from": admin})
    after = snapshot()

    print(before)
    print(after)

    print(after["supplied"] - s)
    assert abs(after["supplied"] - s) <= 0.001 * 10 ** DECIMALS
