import brownie
from brownie import StrategyVaultV3Eth
import pytest


@pytest.fixture(scope="module", autouse=True)
def strategy(ethFundManager, admin, treasury):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyVaultV3Eth.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
