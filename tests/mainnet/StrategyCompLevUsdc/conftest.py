import brownie
from brownie import interface, StrategyCompLevUsdc
import pytest


@pytest.fixture(scope="session")
def strategy(usdcFundManager, admin, treasury):
    fundManager = usdcFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyCompLevUsdc.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
