import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest

MIN_PERF_FEE = 100
MAX_PERF_FEE = 2000


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, strategyTest):
    pass


def test_calc_perf_fee_min_max(strategyTest):
    strategy = strategyTest

    # min tvl, max perf fee
    tvl = strategy.minTvl()
    calc = strategy.calcPerfFee(tvl)
    assert calc == MAX_PERF_FEE

    # max tvl, min perf fee
    tvl = strategy.maxTvl()
    calc = strategy.calcPerfFee(tvl)
    assert calc == MIN_PERF_FEE


@given(
    tvl=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    minTvl=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
    maxTvl=strategy("uint256", min_value=0, max_value=2 ** 128 - 1),
)
def test_calc_perf_fee(strategyTest, admin, tvl, minTvl, maxTvl):
    strategy = strategyTest

    _minTvl = min(minTvl, maxTvl)
    _maxTvl = max(minTvl, maxTvl) + 1

    strategy.setMinMaxTvl(_minTvl, _maxTvl, {"from": admin})

    calc = strategy.calcPerfFee(tvl)

    assert calc <= MAX_PERF_FEE
    assert calc >= MIN_PERF_FEE

    if tvl <= _minTvl:
        assert calc == MAX_PERF_FEE
    elif tvl < _maxTvl:
        dy = MAX_PERF_FEE - MIN_PERF_FEE
        dx = _maxTvl - _minTvl
        expected = MAX_PERF_FEE - (dy * (tvl - _minTvl) / dx)

        # print("expected", expected)
        # print("calc", calc)

        assert abs(calc - expected) <= 1
    else:
        assert calc == MIN_PERF_FEE
