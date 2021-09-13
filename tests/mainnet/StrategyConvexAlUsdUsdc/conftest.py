import brownie
from brownie import interface, StrategyConvexAlUsdUsdc
import pytest


@pytest.fixture(scope="session")
def strategy(usdcVault, admin, treasury):
    vault = usdcVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexAlUsdUsdc.deploy(
        vault, treasury, 0, 2 ** 256 - 1, {"from": admin}
    )

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
