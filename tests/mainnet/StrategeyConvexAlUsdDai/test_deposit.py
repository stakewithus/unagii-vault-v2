import brownie
from brownie import StrategyConvexAlUsdDai
import pytest


def test_deposit(daiFundManager, admin, treasury, dai, dai_whale):
    token = dai
    whale = dai_whale

    fundManager = daiFundManager
    timeLock = fundManager.timeLock()

    strategy = StrategyConvexAlUsdDai.deploy(fundManager, treasury, {"from": admin})

    fundManager.approveStrategy(strategy, {"from": timeLock})
    fundManager.addStrategyToQueue(strategy, 1, 0, 2 ** 256 - 1, {"from": admin})

    amount = 10 ** 18
    token.transfer(fundManager, amount, {"from": whale})

    strategy.deposit(2 ** 256 - 1, 1, {"from": admin})

    print(dai.balanceOf(dai_whale))