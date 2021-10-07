import brownie
from brownie import StrategyConvexAlUsdUsdt
import pytest


@pytest.fixture(scope="session")
def strategy(usdtVault, admin, treasury):
    vault = usdtVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexAlUsdUsdt.deploy(vault, treasury, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
