import brownie
import pytest


def test_leverage(strategy, admin, dai, dai_whale):
    token = dai
    whale = dai_whale

    deposit_amount = 10 ** 18
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
    tx = strategy.leverage(s, {"from": admin})
    after = snapshot()

    print(before)
    print(after)
    # # for e in tx.events:
    # #     print(e)

    assert abs(after["supplied"] - s) <= 0.001 * 10 ** 18
