import brownie
from brownie import StrategyConvexObtcWbtc
import pytest


@pytest.fixture(scope="session")
def strategy(wbtcVault, admin, treasury):
    vault = wbtcVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexObtcWbtc.deploy(
        vault, treasury, 0, 2 ** 256 - 1, {"from": admin}
    )

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
