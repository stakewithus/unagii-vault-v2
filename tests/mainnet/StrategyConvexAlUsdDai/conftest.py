import brownie
from brownie import interface, StrategyConvexAlUsdDai
import pytest


@pytest.fixture(scope="session")
def strategy(daiVault, admin, treasury):
    vault = daiVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexAlUsdDai.deploy(
        vault, treasury, 0, 2 ** 256 - 1, {"from": admin}
    )

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
