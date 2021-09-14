import brownie

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_init(EthVault, uEth, admin, guardian, worker):
    vault = EthVault.deploy(uEth, guardian, worker, {"from": admin})

    assert vault.timeLock() == admin
    assert vault.admin() == admin
    assert vault.guardian() == guardian
    assert vault.worker() == worker
    assert vault.token() == ETH
    assert vault.uToken() == uEth

    assert vault.paused()
    assert vault.blockDelay() >= 1
    assert vault.lockedProfitDegradation() > 0
    assert vault.lastSync() > 0
    assert vault.minReserve() > 0
    assert vault.minReserve() <= 10000
