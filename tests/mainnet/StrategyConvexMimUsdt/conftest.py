import brownie
from brownie import interface, StrategyConvexMimUsdt
import pytest


@pytest.fixture(scope="session")
def strategy(usdtFundManager, admin, treasury):
    fundManager = usdtFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyConvexMimUsdt.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
