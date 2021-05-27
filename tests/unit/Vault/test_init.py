import brownie


def test_init(vault, token, uToken, admin, timeLock, guardian, keeper):
    assert vault.admin() == admin
    assert vault.timeLock() == timeLock
    assert vault.guardian() == guardian
    assert vault.keeper() == keeper

    assert vault.token() == token.address
    assert vault.uToken() == uToken.address

    assert vault.paused()
    assert vault.blockDelay() > 0
    assert vault.lastReport() > 0
    assert vault.lockedProfitDegradation() > 0