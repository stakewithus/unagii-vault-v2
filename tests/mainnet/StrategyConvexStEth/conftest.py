import brownie
from brownie import interface, StrategyConvexStEth
import pytest


@pytest.fixture(scope="session")
def strategy(ethFundManager, admin, treasury):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyConvexStEth.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
