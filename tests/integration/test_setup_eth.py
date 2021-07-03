import brownie
import pytest


def test_setup_eth(setup_eth, uEth, ethVault, timeLock, ethFundManager, admin):
    fundManager = ethFundManager
    vault = ethVault

    assert uEth.minter() == vault
    assert uEth.nextTimeLock() == timeLock
    assert uEth.timeLock() == timeLock

    assert fundManager.vault() == vault
    assert fundManager.nextTimeLock() == timeLock
    assert fundManager.timeLock() == timeLock

    assert vault.fundManager() == fundManager
    assert vault.nextTimeLock() == timeLock
    assert vault.timeLock() == timeLock