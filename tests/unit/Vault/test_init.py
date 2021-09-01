import brownie


def test_init(Vault, token, uToken, TestToken, admin, guardian, worker):
    _token = TestToken.deploy("test", "TEST", 18, {"from": admin})

    with brownie.reverts("uToken token != token"):
        Vault.deploy(_token, uToken, guardian, worker, {"from": admin})

    vault = Vault.deploy(token, uToken, guardian, worker, {"from": admin})

    assert vault.timeLock() == admin
    assert vault.admin() == admin
    assert vault.guardian() == guardian
    assert vault.worker() == worker
    assert vault.token() == token
    assert vault.uToken() == uToken

    assert vault.paused()
    assert vault.blockDelay() >= 1
    assert vault.lockedProfitDegradation() > 0
    assert vault.minReserve() > 0
    assert vault.minReserve() <= 10000
