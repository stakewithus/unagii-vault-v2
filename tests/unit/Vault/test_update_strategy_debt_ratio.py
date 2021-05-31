import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_update_strategy_debt_ratio(vault, strategy, admin, timeLock, keeper, user):
    # not authorized
    with brownie.reverts("!auth"):
        vault.updateStrategyDebtRatio(strategy.address, 0, {"from": user})

    # not active
    with brownie.reverts("!active"):
        vault.updateStrategyDebtRatio(strategy.address, 0, {"from": admin})

    vault.approveStrategy(strategy.address, 0, 0, 0, {"from": timeLock})
    vault.addStrategyToQueue(strategy.address, 0, {"from": admin})

    # total debt ratio > max
    with brownie.reverts("total > max"):
        vault.updateStrategyDebtRatio(strategy.address, 10001, {"from": admin})

    totalDebtRatio = vault.totalDebtRatio()
    vault.updateStrategyDebtRatio(strategy.address, 123, {"from": keeper})
    assert vault.strategies(strategy.address)["debtRatio"] == 123
    assert vault.totalDebtRatio() == totalDebtRatio + 123
