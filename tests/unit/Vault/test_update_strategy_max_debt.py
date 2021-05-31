import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_update_strategy_max_debt_per_harvest(
    vault, strategy, admin, timeLock, keeper, user
):
    # not authorized
    with brownie.reverts("!auth"):
        vault.updateStrategyMaxDebtPerHarvest(strategy.address, 0, {"from": user})

    # not approved
    with brownie.reverts("!approved"):
        vault.updateStrategyMaxDebtPerHarvest(strategy.address, 0, {"from": admin})

    vault.approveStrategy(strategy.address, 1, 1, 0, {"from": timeLock})

    # max < min
    with brownie.reverts("max < min"):
        vault.updateStrategyMaxDebtPerHarvest(strategy.address, 0, {"from": admin})

    vault.updateStrategyMaxDebtPerHarvest(strategy.address, 2, {"from": keeper})
    assert vault.strategies(strategy.address)["maxDebtPerHarvest"] == 2
