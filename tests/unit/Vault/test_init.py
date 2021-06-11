import brownie


def test_init(Vault, token, uToken, admin, guardian):
    vault = Vault.deploy(token, uToken, guardian, {"from": admin})

    assert vault.timeLock() == admin
    assert vault.admin() == admin
    assert vault.guardian() == guardian

    assert vault.token() == token.address
    assert vault.uToken() == uToken.address

    assert vault.paused()
    assert vault.blockDelay() > 0
    assert vault.minReserve() > 0 and vault.minReserve() <= 10000
    assert vault.lastReport() > 0
    assert vault.lockedProfitDegradation() > 0