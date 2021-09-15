import brownie
from brownie import ZERO_ADDRESS


def test_setup(setup_eth, uEth, ethVault, timeLock, admin):
    assert uEth.minter() == ethVault
    assert uEth.nextTimeLock() == ZERO_ADDRESS
    assert uEth.timeLock() == timeLock

    assert ethVault.nextTimeLock() == ZERO_ADDRESS
    assert ethVault.timeLock() == timeLock
    assert ethVault.admin() == admin