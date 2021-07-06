import brownie
from brownie import interface, StrategyCompLevDai
import pytest


@pytest.fixture(scope="session")
def strategy(daiFundManager, admin, treasury):
    fundManager = daiFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyCompLevDai.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
