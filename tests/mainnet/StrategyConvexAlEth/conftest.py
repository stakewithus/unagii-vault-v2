import brownie
from brownie import interface, StrategyConvexAlEth
import pytest


@pytest.fixture(scope="session")
def strategy(ethFundManager, admin, treasury):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyConvexAlEth.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
