import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_update_strategy_perf_fee(vault, strategy, admin, timeLock, keeper, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.updateStrategyPerformanceFee(strategy.address, 0, {"from": user})

    # not approved
    with brownie.reverts("!approved"):
        vault.updateStrategyPerformanceFee(strategy.address, 0, {"from": admin})

    vault.approveStrategy(strategy.address, 1, 1, 0, {"from": timeLock})

    # perf fee > max
    with brownie.reverts("perf fee > max"):
        vault.updateStrategyPerformanceFee(strategy.address, 5001, {"from": admin})

    vault.updateStrategyPerformanceFee(strategy.address, 2, {"from": admin})
    assert vault.strategies(strategy.address)["perfFee"] == 2
