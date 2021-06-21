import brownie
from brownie import ZERO_ADDRESS


def test_init_no_old_vault(Vault, token, uToken, admin, guardian):
    vault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})

    assert vault.timeLock() == admin
    assert vault.admin() == admin
    assert vault.guardian() == guardian

    assert vault.token() == token.address
    assert vault.uToken() == uToken.address

    assert vault.state() == 0
    assert vault.blockDelay() > 0
    assert vault.minReserve() > 0 and vault.minReserve() <= 10000
    assert vault.lastReport() == 0
    assert vault.lockedProfitDegradation() > 0

    assert vault.oldVault() == ZERO_ADDRESS


def test_init_old_vault(Vault, token, uToken, TestToken, UnagiiToken, admin, guardian):
    _token = TestToken.deploy("test", "TEST", 18, {"from": admin})
    _uToken = UnagiiToken.deploy(_token, {"from": admin})

    with brownie.reverts("old vault token != token"):
        oldVault = Vault.deploy(
            _token, _uToken, guardian, ZERO_ADDRESS, {"from": admin}
        )
        newVault = Vault.deploy(token, uToken, guardian, oldVault, {"from": admin})

    with brownie.reverts("old vault uToken != uToken"):
        _uToken = UnagiiToken.deploy(token, {"from": admin})
        oldVault = Vault.deploy(token, _uToken, guardian, ZERO_ADDRESS, {"from": admin})
        newVault = Vault.deploy(token, uToken, guardian, oldVault, {"from": admin})

    oldVault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})
    newVault = Vault.deploy(token, uToken, guardian, oldVault, {"from": admin})

    assert newVault.oldVault() == oldVault
