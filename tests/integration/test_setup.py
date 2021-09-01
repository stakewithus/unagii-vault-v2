import brownie
from brownie import ZERO_ADDRESS


def test_setup(setup, uToken, vault, timeLock, admin):
    assert uToken.minter() == vault
    assert uToken.nextTimeLock() == ZERO_ADDRESS
    assert uToken.timeLock() == timeLock

    assert vault.nextTimeLock() == ZERO_ADDRESS
    assert vault.timeLock() == timeLock
    assert vault.admin() == admin