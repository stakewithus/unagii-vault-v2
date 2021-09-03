from brownie.test import given, strategy
import pytest

MIN_PERF_FEE = 100
MAX_PERF_FEE = 2000
PERF_FEE_DENOMINATOR = 10000


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


@given(
    profit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    minProfit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    maxProfit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
)
def test_calc_fee(perfFeeTest, user, profit, minProfit, maxProfit):
    _minProfit = min(minProfit, maxProfit)
    _maxProfit = max(minProfit, maxProfit) + 1

    perfFeeTest.setMinMaxProfit(_minProfit, _maxProfit, {"from": user})

    fee = perfFeeTest.calcFee(profit)

    if profit > 0:
        print("fee / profit", fee / profit)

    # allowed rounding error
    ERROR = 1

    assert fee <= profit * (MAX_PERF_FEE + ERROR) / PERF_FEE_DENOMINATOR
    assert fee >= profit * (MIN_PERF_FEE - ERROR) / PERF_FEE_DENOMINATOR
