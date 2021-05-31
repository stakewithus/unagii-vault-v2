import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_update_strategy_min_debt_per_harvest(
    vault, strategy, admin, timeLock, keeper, user
):
    # not authorized
    with brownie.reverts("!auth"):
        vault.updateStrategyMinDebtPerHarvest(strategy.address, 0, {"from": user})

    # not approved
    with brownie.reverts("!approved"):
        vault.updateStrategyMinDebtPerHarvest(strategy.address, 0, {"from": admin})

    vault.approveStrategy(strategy.address, 0, 1, 0, {"from": timeLock})

    # min > max
    with brownie.reverts("min > max"):
        vault.updateStrategyMinDebtPerHarvest(strategy.address, 2, {"from": admin})

    vault.updateStrategyMinDebtPerHarvest(strategy.address, 1, {"from": keeper})
    assert vault.strategies(strategy.address)["minDebtPerHarvest"] == 1
