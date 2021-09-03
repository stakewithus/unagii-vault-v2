from brownie.test import given, strategy
import pytest

MIN_PERF_FEE = 100
MAX_PERF_FEE = 2000


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_calc_perf_fee_min_max(perfFeeTest, user):
    minProfit = 1
    maxProfit = 1000
    perfFeeTest.setMinMaxProfit(minProfit, maxProfit, {"from": user})

    # min profit, max perf fee
    calc = perfFeeTest.calcPerfFee(minProfit)
    assert calc == MAX_PERF_FEE

    # max profit, min perf fee
    calc = perfFeeTest.calcPerfFee(maxProfit)
    assert calc == MIN_PERF_FEE


@given(
    profit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    minProfit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    maxProfit=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
)
def test_calc_perf_fee(perfFeeTest, user, profit, minProfit, maxProfit):
    _minProfit = min(minProfit, maxProfit)
    _maxProfit = max(minProfit, maxProfit) + 1

    perfFeeTest.setMinMaxProfit(_minProfit, _maxProfit, {"from": user})

    calc = perfFeeTest.calcPerfFee(profit)

    assert calc <= MAX_PERF_FEE
    assert calc >= MIN_PERF_FEE

    if profit <= _minProfit:
        assert calc == MAX_PERF_FEE
    elif profit < _maxProfit:
        dy = MAX_PERF_FEE - MIN_PERF_FEE
        dx = _maxProfit - _minProfit
        expected = MAX_PERF_FEE - (dy * (profit - _minProfit) / dx)

        # print("expected", expected)
        # print("calc", calc)

        assert abs(calc - expected) <= 1
    else:
        assert calc == MIN_PERF_FEE
