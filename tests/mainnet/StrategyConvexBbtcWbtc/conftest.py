import brownie
from brownie import StrategyConvexBbtcWbtc
import pytest


@pytest.fixture(scope="session")
def strategy(wbtcVault, admin, treasury):
    vault = wbtcVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexBbtcWbtc.deploy(vault, treasury, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
