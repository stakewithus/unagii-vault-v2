import brownie
from brownie import StrategyConvexSbtcWbtc
import pytest


@pytest.fixture(scope="session")
def strategy(wbtcVault, admin, treasury):
    vault = wbtcVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexSbtcWbtc.deploy(vault, treasury, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
