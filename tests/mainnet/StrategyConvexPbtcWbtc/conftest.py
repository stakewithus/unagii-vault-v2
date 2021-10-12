import brownie
from brownie import interface, StrategyConvexPbtcWbtc
import pytest


@pytest.fixture(scope="session")
def strategy(wbtcFundManager, admin, treasury):
    fundManager = wbtcFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyConvexPbtcWbtc.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
