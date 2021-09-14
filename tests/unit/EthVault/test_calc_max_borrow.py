from brownie import ZERO_ADDRESS, TestStrategyEth
from brownie.test import given, strategy

N = 2  # active strategies
MIN_RESERVE_DENOMINATOR = 10000
ERROR = 1  # rounding error


@given(
    deposit_amount=strategy("uint256", min_value=100, max_value=1000),
)
def test_calc_min_reserve(ethVault, admin, deposit_amount):
    vault = ethVault
    timeLock = vault.timeLock()

    # deposit_amount = 1000
    admin.transfer(vault, deposit_amount)
    total = deposit_amount

    strats = []
    debtRatios = []
    for i in range(N):
        strat = TestStrategyEth.deploy(vault, {"from": admin})

        vault.approveStrategy(strat, {"from": timeLock})

        debtRatio = 100 * (i + 1)
        vault.activateStrategy(strat, debtRatio, {"from": admin})

        debtRatios.append(debtRatio)
        strats.append(strat)

    # calc max borrow when debt = 0
    minReserve = vault.minReserve()
    totalDebtRatio = vault.totalDebtRatio()

    free = total * (MIN_RESERVE_DENOMINATOR - minReserve) / MIN_RESERVE_DENOMINATOR

    # test debt = 0
    total_calc = 0
    for i in range(N):
        strat = strats[i]
        debtRatio = debtRatios[i]

        calc = vault.calcMaxBorrow(strat)
        assert abs(calc - free * debtRatio / totalDebtRatio) <= ERROR

        total_calc += calc

    assert abs(total_calc - free) <= ERROR

    # bororw and test calc max borrow = 0
    for i in range(N):
        strat = strats[i]

        vault.borrow(2 ** 256 - 1, {"from": strat})
        calc = vault.calcMaxBorrow(strat)
        assert calc == 0

    # test debt > 0 and debt < limit
    admin.transfer(vault, deposit_amount)
    total += deposit_amount

    free = total * (MIN_RESERVE_DENOMINATOR - minReserve) / MIN_RESERVE_DENOMINATOR

    for i in range(N):
        strat = strats[i]
        debtRatio = debtRatios[i]

        calc = vault.calcMaxBorrow(strat)
        debt = vault.strategies(strat)["debt"]
        limit = free * debtRatio / totalDebtRatio

        assert abs(calc - (limit - debt)) <= ERROR
