import brownie
from brownie import interface, StrategyConvexAlUsdUsdt
import pytest


@pytest.fixture(scope="session")
def strategy(usdtVault, admin, treasury):
    vault = usdtVault
    timeLock = vault.timeLock()

    strategy = StrategyConvexAlUsdUsdt.deploy(
        vault, treasury, 0, 2 ** 256 - 1, {"from": admin}
    )

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 100, {"from": admin})

    yield strategy
