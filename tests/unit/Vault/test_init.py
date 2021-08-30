import brownie


def test_init(Vault, token, uToken, TestToken, admin):
    _token = TestToken.deploy("test", "TEST", 18, {"from": admin})

    with brownie.reverts("uToken token != token"):
        Vault.deploy(_token, uToken, {"from": admin})

    vault = Vault.deploy(token, uToken, {"from": admin})

    assert vault.timeLock() == admin
    assert vault.admin() == admin
    assert vault.guardian() == admin
    assert vault.worker() == admin
    assert vault.token() == token
    assert vault.uToken() == uToken

    assert vault.paused()
    assert vault.blockDelay() >= 1
    assert vault.lockedProfitDegradation() > 0
    assert vault.minReserve() > 0
    assert vault.minReserve() <= 10000
