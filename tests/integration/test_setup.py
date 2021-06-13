import brownie
import pytest


def test_setup(setup, uToken, vault, timeLock, fundManager, admin):
    assert uToken.minter() == vault
    assert uToken.nextTimeLock() == timeLock
    assert uToken.timeLock() == timeLock

    assert fundManager.vault() == vault
    assert fundManager.nextTimeLock() == timeLock
    assert fundManager.timeLock() == timeLock

    assert vault.fundManager() == fundManager
    assert vault.nextTimeLock() == timeLock
    assert vault.timeLock() == timeLock