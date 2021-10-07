import brownie
from brownie import StrategyConvexStEth
import pytest


@pytest.fixture(scope="session")
def strategy(ethVault, admin, treasury):
    vault = ethVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexStEth.deploy(vault, treasury, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
