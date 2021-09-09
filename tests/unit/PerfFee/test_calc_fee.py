from brownie.test import given, strategy
import pytest

MIN_PERF_FEE = 100
MAX_PERF_FEE = 2000
PERF_FEE_DENOMINATOR = 10000


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_calc_perf_fee_min_max(perfFeeTest, user):
    minProfit = 100
    maxProfit = 1000
    perfFeeTest.setMinMaxProfit(minProfit, maxProfit, {"from": user})

    # min profit, max perf fee
    calc = perfFeeTest.calcPerfFee(minProfit)
    assert calc == MAX_PERF_FEE * minProfit / PERF_FEE_DENOMINATOR

    # max profit, min perf fee
    calc = perfFeeTest.calcPerfFee(maxProfit)
    assert calc == MIN_PERF_FEE * maxProfit / PERF_FEE_DENOMINATOR


@given(
    profit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    minProfit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    maxProfit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
)
def test_calc_perf_fee(perfFeeTest, user, profit, minProfit, maxProfit):
    _minProfit = min(minProfit, maxProfit)
    _maxProfit = max(minProfit, maxProfit) + 1

    perfFeeTest.setMinMaxProfit(_minProfit, _maxProfit, {"from": user})

    fee = perfFeeTest.calcPerfFee(profit)

    if profit > 0:
        print("fee / profit", fee / profit)

    # allowed rounding error
    ERROR = 1

    assert fee <= profit * (MAX_PERF_FEE + ERROR) / PERF_FEE_DENOMINATOR
    assert fee >= profit * (MIN_PERF_FEE - ERROR) / PERF_FEE_DENOMINATOR
