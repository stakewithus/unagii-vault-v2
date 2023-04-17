import brownie
from brownie import StrategyVaultV3Usdc
import pytest


@pytest.fixture(scope="module", autouse=True)
def strategy(usdcFundManager, admin, treasury):
    fundManager = usdcFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyVaultV3Usdc.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    yield strategy
