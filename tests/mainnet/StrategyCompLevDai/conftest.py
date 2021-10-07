import brownie
from brownie import StrategyCompLevDai
import pytest


@pytest.fixture(scope="session")
def strategy(daiVault, admin, treasury):
    vault = daiVault
    timeLock = vault.timeLock()

    strategy = StrategyCompLevDai.deploy(vault, treasury, {"from": admin})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
