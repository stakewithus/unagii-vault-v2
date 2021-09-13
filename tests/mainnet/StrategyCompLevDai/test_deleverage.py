import brownie
import pytest

DECIMALS = 18


def test_deleverage(strategy, daiVault, admin, dai, dai_whale):
    token = dai
    whale = dai_whale
    vault = daiVault

    deposit_amount = 10 ** DECIMALS
    token.transfer(vault, deposit_amount, {"from": whale})

    calc = vault.calcMaxBorrow(strategy)
    assert calc > 0

    # transfer to strategy
    strategy.deposit(2 ** 256 - 1, calc, {"from": admin})

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
    strategy.deleverage(s, {"from": admin})
    after = snapshot()

    print(before)
    print(after)

    assert abs(after["supplied"] - s) <= 0.001 * 10 ** DECIMALS
