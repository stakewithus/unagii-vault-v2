import brownie
from brownie import ZERO_ADDRESS

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_init_no_old_vault(EthVault, uEth, admin, guardian):
    vault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})

    assert vault.timeLock() == admin
    assert vault.admin() == admin
    assert vault.guardian() == guardian

    assert vault.token() == ETH
    assert vault.uToken() == uEth.address

    assert vault.paused() == True
    assert vault.initialized() == False
    assert vault.blockDelay() > 0
    assert vault.minReserve() > 0 and vault.minReserve() <= 10000
    assert vault.lastReport() == 0
    assert vault.lockedProfitDegradation() > 0

    assert vault.oldVault() == ZERO_ADDRESS


def test_init_old_vault(EthVault, uEth, TestToken, UnagiiToken, admin, guardian):
    with brownie.reverts("old vault uToken != uToken"):
        _uEth = UnagiiToken.deploy(ETH, {"from": admin})
        oldVault = EthVault.deploy(_uEth, guardian, ZERO_ADDRESS, {"from": admin})
        newVault = EthVault.deploy(uEth, guardian, oldVault, {"from": admin})

    oldVault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})
    newVault = EthVault.deploy(uEth, guardian, oldVault, {"from": admin})

    assert newVault.oldVault() == oldVault
